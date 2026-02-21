"""Validation engine - rules-based compliance checking."""
import re
from typing import List

from app.models.schemas import ExtractedField, ValidationResult


class ValidationEngine:
    """Validate extracted fields against compliance rules."""

    @staticmethod
    def _is_vague_description(description: str) -> bool:
        """Check if description is too vague."""
        vague_terms = ["goods", "products", "items", "stuff", "merchandise", "cargo"]
        desc_lower = description.lower().strip()
        return desc_lower in vague_terms or len(desc_lower) < 5

    def validate(
        self,
        extracted_fields: list[ExtractedField],
    ) -> list[ValidationResult]:
        """
        Validate extracted fields against compliance rules.

        Args:
            extracted_fields: Fields extracted from documents

        Returns:
            List of validation results
        """
        results: list[ValidationResult] = []

        # Convert to dict for easier lookup
        field_map = {f.name: f.value for f in extracted_fields}
        
        # Determine document type
        doc_type = field_map.get("_document_type", "unknown")
        
        # Invoice-specific validations
        if doc_type == "invoice":
            results.extend(self._validate_invoice_fields(field_map))
        
        # Packing list specific validations  
        elif doc_type == "packing_list":
            results.extend(self._validate_packing_list_fields(field_map))
        
        # Common validations for both document types
        results.extend(self._validate_common_fields(field_map, doc_type))
        
        return results

    def _validate_invoice_fields(self, field_map: dict) -> list[ValidationResult]:
        """Validate invoice-specific fields."""
        results = []
        
        # Invoice value required for invoices
        invoice_value = field_map.get("invoice_value")
        has_value = bool(invoice_value) and bool(re.search(r"\d+", str(invoice_value)))
        results.append(
            ValidationResult(
                field_name="invoice_value",
                passed=has_value,
                error_message=None if has_value else "Total invoice value missing",
            )
        )
        
        # Invoice date required for invoices
        invoice_date = field_map.get("invoice_date")
        has_date = bool(invoice_date)
        results.append(
            ValidationResult(
                field_name="invoice_date",
                passed=has_date,
                error_message=None if has_date else "Missing required date (invoice date)",
            )
        )
        
        # HS code required for invoices
        hs_code = field_map.get("hs_code")
        if hs_code:
            hs_valid = bool(re.match(r"^\d{6,10}$", str(hs_code)))
        else:
            hs_valid = False
        results.append(
            ValidationResult(
                field_name="hs_code",
                passed=hs_valid,
                error_message=None if hs_valid else "HS code missing or invalid (must be 6-10 digits)",
            )
        )
        
        # Product description required for invoices
        product_desc = field_map.get("product_description")
        if product_desc:
            desc_valid = len(str(product_desc)) > 5 and not self._is_vague_description(str(product_desc))
        else:
            desc_valid = False
        results.append(
            ValidationResult(
                field_name="product_description",
                passed=desc_valid,
                error_message=None if desc_valid else "Product description too vague",
            )
        )
        
        return results
    
    def _validate_packing_list_fields(self, field_map: dict) -> list[ValidationResult]:
        """Validate packing list-specific fields."""
        results = []
        
        # Date required (but not necessarily invoice_date)
        doc_date = field_map.get("date") or field_map.get("invoice_date")
        has_date = bool(doc_date)
        results.append(
            ValidationResult(
                field_name="document_date",
                passed=has_date,
                error_message=None if has_date else "Missing document date",
            )
        )
        
        # Item count for packing list
        item_count = field_map.get("item_count")
        has_items = bool(item_count) and int(item_count) > 0
        results.append(
            ValidationResult(
                field_name="item_count",
                passed=has_items,
                error_message=None if has_items else "Packing list is missing item count",
            )
        )
        
        return results
    
    def _validate_common_fields(self, field_map: dict, doc_type: str) -> list[ValidationResult]:
        """Validate fields common to both document types."""
        results = []
        
        # Shipper name
        shipper_name = field_map.get("shipper_name")
        has_shipper_name = bool(shipper_name) and len(str(shipper_name)) > 2
        results.append(
            ValidationResult(
                field_name="shipper_name",
                passed=has_shipper_name,
                error_message=None if has_shipper_name else "Shipper name incomplete",
            )
        )
        
        # Shipper address (only if name is present)
        if has_shipper_name:
            shipper_address = field_map.get("shipper_address")
            has_shipper_addr = bool(shipper_address) and len(str(shipper_address)) > 10
            results.append(
                ValidationResult(
                    field_name="shipper_address",
                    passed=has_shipper_addr,
                    error_message=None if has_shipper_addr else "Shipper address incomplete",
                )
            )
        
        # Consignee name
        consignee_name = field_map.get("consignee_name")
        has_consignee_name = bool(consignee_name) and len(str(consignee_name)) > 2
        results.append(
            ValidationResult(
                field_name="consignee_name",
                passed=has_consignee_name,
                error_message=None if has_consignee_name else "Consignee name incomplete",
            )
        )
        
        # Consignee address (only if name is present)
        if has_consignee_name:
            consignee_address = field_map.get("consignee_address")
            has_consignee_addr = bool(consignee_address) and len(str(consignee_address)) > 10
            results.append(
                ValidationResult(
                    field_name="consignee_address",
                    passed=has_consignee_addr,
                    error_message=None if has_consignee_addr else "Consignee address incomplete",
                )
            )
        
        return results

    def validate_cross_document(
        self,
        invoice_fields: list[ExtractedField],
        packing_list_fields: list[ExtractedField],
    ) -> list[ValidationResult]:
        """
        Validate consistency between invoice and packing list.

        Args:
            invoice_fields: Fields from invoice
            packing_list_fields: Fields from packing list

        Returns:
            List of cross-document validation results
        """
        results: list[ValidationResult] = []
        
        invoice_map = {f.name: f.value for f in invoice_fields}
        packing_map = {f.name: f.value for f in packing_list_fields}

        # Check invoice number match
        inv_no = invoice_map.get("invoice_no")
        pack_inv_no = packing_map.get("invoice_no")
        if inv_no and pack_inv_no:
            results.append(
                ValidationResult(
                    field_name="invoice_number_match",
                    passed=inv_no == pack_inv_no,
                    error_message=None if inv_no == pack_inv_no else f"Invoice number mismatch: {inv_no} vs {pack_inv_no}",
                )
            )

        # Check item count match
        inv_count = invoice_map.get("item_count")
        pack_count = packing_map.get("item_count")
        if inv_count and pack_count:
            results.append(
                ValidationResult(
                    field_name="item_count_match",
                    passed=inv_count == pack_count,
                    error_message=None if inv_count == pack_count else f"Item count mismatch: invoice has {inv_count}, packing list has {pack_count}",
                )
            )
        elif inv_count and not pack_count:
            results.append(
                ValidationResult(
                    field_name="item_count_match",
                    passed=False,
                    error_message="Packing list is missing item count",
                )
            )
        elif pack_count and not inv_count:
            results.append(
                ValidationResult(
                    field_name="item_count_match",
                    passed=False,
                    error_message="Invoice is missing item count",
                )
            )

        # Check shipper consistency
        inv_shipper = invoice_map.get("shipper_name")
        pack_shipper = packing_map.get("shipper_name")
        if inv_shipper and pack_shipper:
            shipper_match = self._fuzzy_match(inv_shipper, pack_shipper)
            results.append(
                ValidationResult(
                    field_name="shipper_consistency",
                    passed=shipper_match,
                    error_message=None if shipper_match else "Shipper name inconsistent between documents",
                )
            )

        # Check consignee consistency
        inv_consignee = invoice_map.get("consignee_name")
        pack_consignee = packing_map.get("consignee_name")
        if inv_consignee and pack_consignee:
            consignee_match = self._fuzzy_match(inv_consignee, pack_consignee)
            results.append(
                ValidationResult(
                    field_name="consignee_consistency",
                    passed=consignee_match,
                    error_message=None if consignee_match else "Consignee name inconsistent between documents",
                )
            )

        return results

    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.7) -> bool:
        """Simple fuzzy string matching."""
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # Exact match
        if s1 == s2:
            return True
        
        # One contains the other
        if s1 in s2 or s2 in s1:
            return True
        
        # Simple similarity: common words ratio
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return False
        
        common = words1 & words2
        similarity = len(common) / max(len(words1), len(words2))
        
        return similarity >= threshold
