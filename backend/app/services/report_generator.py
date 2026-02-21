"""Report generator - format results with fix instructions."""
from datetime import datetime

from app.models.schemas import (
    ComplianceReport,
    ExtractedField,
    ValidationResult,
)


class ReportGenerator:
    """Generate human-readable compliance reports."""

    # Fix instructions in Chinese for user-friendly guidance
    FIX_INSTRUCTIONS = {
        "hs_code": "请在发票和装箱单上添加6-10位的HS编码",
        "invoice_value": "请填写发票总金额及币种（如：USD 10,000）",
        "shipper_name": "请填写完整的发货人（出口商）名称",
        "consignee_name": "请填写完整的收货人（进口商）名称",
        "consignee_address": "请填写完整的收货人地址，包括城市、国家和邮编",
        "product_description": "请提供更详细的产品描述，避免使用\"goods\"、\"products\"等笼统词汇",
        "invoice_date": "请填写发票日期",
        "item_count_mismatch": "请核对发票和装箱单的品项数量是否一致",
    }

    def generate(
        self,
        document_id: str,
        extracted_fields: list[ExtractedField],
        validations: list[ValidationResult],
    ) -> ComplianceReport:
        """
        Generate a compliance report.

        Args:
            document_id: Unique document identifier
            extracted_fields: Extracted fields from documents
            validations: Validation results

        Returns:
            Complete compliance report
        """
        failed_validations = [v for v in validations if not v.passed]
        overall_status = "fail" if failed_validations else "pass"

        # Generate fix instructions for failed validations
        fix_instructions: list[str] = []
        for v in failed_validations:
            instruction = self.FIX_INSTRUCTIONS.get(v.field_name)
            if instruction:
                fix_instructions.append(f"• {v.field_name}: {instruction}")

        return ComplianceReport(
            document_id=document_id,
            overall_status=overall_status,
            created_at=datetime.utcnow(),
            extracted_fields=extracted_fields,
            validations=validations,
            fix_instructions=fix_instructions,
        )

    def generate_pdf(self, report: ComplianceReport) -> bytes:
        """
        Generate PDF version of the report.

        Args:
            report: Compliance report

        Returns:
            PDF file content as bytes
        """
        # TODO: Implement PDF generation
        return b""
