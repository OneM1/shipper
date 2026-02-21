"""Document parsing service - OCR and structured extraction."""
import re
from typing import BinaryIO

from app.models.schemas import ExtractedField


class DocumentParser:
    """Parse documents using OCR and structured extraction."""

    async def parse_document(
        self,
        file: BinaryIO,
        document_type: str,
    ) -> list[ExtractedField]:
        """Parse a document and extract key fields."""
        text = self._extract_text_from_pdf(file)
        
        if not text or len(text.strip()) < 50:
            return [
                ExtractedField(name="_error", value="PDF appears to be scanned image.", confidence=1.0),
                ExtractedField(name="_document_type", value=document_type, confidence=1.0),
            ]
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        fields: list[ExtractedField] = []
        
        # Extract basic fields
        invoice_no = self._extract_invoice_number(lines)
        if invoice_no:
            fields.append(ExtractedField(name="invoice_no", value=invoice_no, confidence=0.9))
        
        doc_date = self._extract_date(lines)
        if doc_date:
            date_field = "invoice_date" if document_type == "invoice" else "date"
            fields.append(ExtractedField(name=date_field, value=doc_date, confidence=0.85))
        
        # Extract parties (shipper/consignee)
        parties = self._extract_parties_side_by_side(lines)
        
        if parties.get("shipper_name"):
            fields.append(ExtractedField(name="shipper_name", value=parties["shipper_name"], confidence=0.85))
        if parties.get("shipper_address"):
            fields.append(ExtractedField(name="shipper_address", value=parties["shipper_address"], confidence=0.8))
        if parties.get("consignee_name"):
            fields.append(ExtractedField(name="consignee_name", value=parties["consignee_name"], confidence=0.85))
        if parties.get("consignee_address"):
            fields.append(ExtractedField(name="consignee_address", value=parties["consignee_address"], confidence=0.8))
        
        # Extract items and invoice-specific fields
        if document_type == "invoice":
            items = self._extract_invoice_items(lines)
            if items:
                if items[0].get('hs_code'):
                    fields.append(ExtractedField(name="hs_code", value=items[0]['hs_code'], confidence=0.9))
                if items[0].get('description'):
                    fields.append(ExtractedField(name="product_description", value=items[0]['description'], confidence=0.8))
                fields.append(ExtractedField(name="item_count", value=str(len(items)), confidence=0.9))
            
            value = self._extract_total_value(lines)
            if value:
                fields.append(ExtractedField(name="invoice_value", value=value, confidence=0.85))
        else:
            items = self._extract_packing_items(lines)
            if items:
                fields.append(ExtractedField(name="item_count", value=str(len(items)), confidence=0.9))
        
        fields.append(ExtractedField(name="_document_type", value=document_type, confidence=1.0))
        return fields

    def _extract_text_from_pdf(self, file: BinaryIO) -> str:
        try:
            from pypdf import PdfReader
            file.seek(0)
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception:
            return ""

    def _extract_invoice_number(self, lines: list[str]) -> str:
        for i, line in enumerate(lines):
            if re.search(r"Invoice\s*(?:No|Number|#)[:\s]*$", line, re.IGNORECASE):
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        # Fallback
        for line in lines:
            match = re.search(r"(EXP[\-]\d{4}[\-]\d+)", line, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return ""

    def _extract_date(self, lines: list[str]) -> str:
        for i, line in enumerate(lines):
            if re.search(r"^Date[:\s]*$", line, re.IGNORECASE):
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
            match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if match:
                return match.group(1)
        return ""

    def _extract_parties_side_by_side(self, lines: list[str]) -> dict:
        """Extract shipper/consignee from various formats."""
        result = {
            "shipper_name": "", "shipper_address": "",
            "consignee_name": "", "consignee_address": ""
        }
        
        # Find EXPORTER/SHIPPER and CONSIGNEE indices
        shipper_idx = -1
        consignee_idx = -1
        
        for i, line in enumerate(lines):
            upper = line.upper().rstrip(':')
            
            # Look for SHIPPER/EXPORTER (but not "Exporter Reference")
            if shipper_idx == -1 and (
                upper == "SHIPPER" or 
                upper == "EXPORTER" or 
                upper == "EXPORTER (SHIPPER)" or
                line.startswith("Shipper:") or
                line.startswith("SHIPPER:") or
                line.startswith("EXPORTER (SHIPPER):")
            ):
                if not re.search(r"Reference|Ref\.", line, re.IGNORECASE):
                    shipper_idx = i
            
            # Look for CONSIGNEE (but not "Importer Reference")
            elif consignee_idx == -1 and (
                upper == "CONSIGNEE" or
                upper == "IMPORTER" or 
                upper == "CONSIGNEE (RECEIVER)" or
                line.startswith("Consignee:") or
                line.startswith("CONSIGNEE:") or
                line.startswith("CONSIGNEE (RECEIVER):")
            ):
                if not re.search(r"Reference|Ref\.", line, re.IGNORECASE):
                    consignee_idx = i
        
        if shipper_idx == -1 or consignee_idx == -1:
            return result
        
        # Check format: side-by-side or vertical
        if consignee_idx == shipper_idx + 1:
            # Side-by-side format (FedEx/DHL style):
            # SHIPPER header, CONSIGNEE header, then data alternates
            result = self._parse_side_by_side(lines, shipper_idx, consignee_idx)
        else:
            # Vertical format (original style):
            result = self._parse_vertical(lines, shipper_idx, consignee_idx)
        
        return result
    
    def _parse_side_by_side(self, lines: list[str], shipper_idx: int, consignee_idx: int) -> dict:
        """Parse side-by-side table format."""
        result = {"shipper_name": "", "shipper_address": "", "consignee_name": "", "consignee_address": ""}
        
        data_start = consignee_idx + 1
        
        # Names
        if data_start < len(lines):
            result["shipper_name"] = lines[data_start]
        if data_start + 1 < len(lines):
            result["consignee_name"] = lines[data_start + 1]
        
        # Addresses (interleaved)
        addr_start = data_start + 2
        shipper_lines = []
        consignee_lines = []
        
        for offset in range(0, 6, 2):
            s_idx = addr_start + offset
            c_idx = addr_start + offset + 1
            
            if s_idx < len(lines):
                s_line = lines[s_idx]
                if re.match(r"^(Contact|Tel|Phone|EORI|Tax|Item|Description|No\.)", s_line, re.IGNORECASE):
                    break
                if not self._is_likely_name(s_line):
                    shipper_lines.append(s_line)
            
            if c_idx < len(lines):
                c_line = lines[c_idx]
                if re.match(r"^(Contact|Tel|Phone|EORI|Tax|Item|Description|No\.)", c_line, re.IGNORECASE):
                    break
                if not self._is_likely_name(c_line):
                    consignee_lines.append(c_line)
        
        result["shipper_address"] = ", ".join(shipper_lines)
        result["consignee_address"] = ", ".join(consignee_lines)
        
        return result
    
    def _parse_vertical(self, lines: list[str], shipper_idx: int, consignee_idx: int) -> dict:
        """Parse vertical format (shipper section then consignee section)."""
        result = {"shipper_name": "", "shipper_address": "", "consignee_name": "", "consignee_address": ""}
        
        # Shipper name is right after Shipper: label
        if shipper_idx + 1 < len(lines):
            result["shipper_name"] = lines[shipper_idx + 1]
        
        # Shipper address is next line(s) until Consignee
        shipper_addr_lines = []
        for i in range(shipper_idx + 2, consignee_idx):
            line = lines[i]
            if line and not re.match(r"^(Consignee|Invoice|Date|Item)", line, re.IGNORECASE):
                shipper_addr_lines.append(line)
        result["shipper_address"] = ", ".join(shipper_addr_lines)
        
        # Consignee name is right after Consignee: label
        if consignee_idx + 1 < len(lines):
            result["consignee_name"] = lines[consignee_idx + 1]
        
        # Consignee address is next line(s) until table/item section
        consignee_addr_lines = []
        for i in range(consignee_idx + 2, len(lines)):
            line = lines[i]
            # Stop at table headers or item numbers
            if re.match(r"^(No\.|Description|Item|HS\s*Code|\d+$)", line):
                break
            if line:
                consignee_addr_lines.append(line)
        result["consignee_address"] = ", ".join(consignee_addr_lines)
        
        return result
    
    def _is_likely_name(self, line: str) -> bool:
        """Check if line looks like a company name vs address."""
        # Company names often have these markers
        company_markers = ["Co.", "Ltd.", "Inc.", "LLC", "GmbH", "S.L.", "B.V.", "S.A."]
        for marker in company_markers:
            if marker in line:
                return True
        return False

    def _extract_invoice_items(self, lines: list[str]) -> list[dict]:
        items = []
        
        # Find "Description" header
        desc_idx = -1
        for i, line in enumerate(lines):
            if "Description" in line and i < len(lines) - 1:
                desc_idx = i
                break
        
        if desc_idx == -1:
            return items
        
        # Find first item number
        start_idx = -1
        for i in range(desc_idx + 1, len(lines)):
            if re.match(r"^\d+$", lines[i]):
                start_idx = i
                break
        
        if start_idx == -1:
            return items
        
        # Parse items - each item is 5-6 lines
        i = start_idx
        while i < len(lines):
            if re.match(r"^\d+$", lines[i]):
                item = {"number": lines[i], "description": "", "hs_code": ""}
                
                if i + 1 < len(lines):
                    item["description"] = lines[i + 1]
                if i + 2 < len(lines):
                    potential = lines[i + 2]
                    if re.match(r"^\d{6,10}$", potential):
                        item["hs_code"] = potential
                
                if item["description"]:
                    items.append(item)
                
                i += 5
            else:
                if "TOTAL" in lines[i].upper():
                    break
                i += 1
        
        return items

    def _extract_packing_items(self, lines: list[str]) -> list[dict]:
        items = []
        
        desc_idx = -1
        for i, line in enumerate(lines):
            if "Description" in line:
                desc_idx = i
                break
        
        if desc_idx == -1:
            return items
        
        start_idx = -1
        for i in range(desc_idx + 1, len(lines)):
            if re.match(r"^\d+$", lines[i]):
                start_idx = i
                break
        
        if start_idx == -1:
            return items
        
        i = start_idx
        while i < len(lines):
            if re.match(r"^\d+$", lines[i]):
                if i + 1 < len(lines):
                    items.append({"description": lines[i + 1]})
                i += 6
            else:
                break
        
        return items

    def _extract_total_value(self, lines: list[str]) -> str:
        for i, line in enumerate(lines):
            if re.search(r"^TOTAL[:\s]*$", line, re.IGNORECASE):
                # Look at next few lines for the total value
                for j in range(i + 1, min(i + 3, len(lines))):
                    # Look for USD/EUR followed by number
                    match = re.search(r"USD\s+([\d,]+\.?\d*)", lines[j])
                    if match:
                        return match.group(1).replace(",", "")
                    # Or just a number
                    match = re.search(r"([\d,]+\.\d{2})$", lines[j])
                    if match:
                        return match.group(1).replace(",", "")
        return ""
