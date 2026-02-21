"""PDF report generator service."""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)

from app.models.schemas import ComplianceReport, ExtractedField


class PDFReportGenerator:
    """Generate PDF compliance reports."""

    def generate(self, report: ComplianceReport) -> bytes:
        """
        Generate a PDF compliance report.

        Args:
            report: Compliance report data

        Returns:
            PDF file content as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        # Container for the 'Flowable' objects
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
            alignment=1,  # Center
        )

        header_style = ParagraphStyle(
            "CustomHeader",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=12,
            spaceBefore=12,
        )

        # Title
        elements.append(Paragraph("合规检查报告", title_style))
        elements.append(Paragraph("Compliance Check Report", styles["Heading2"]))
        elements.append(Spacer(1, 0.5 * cm))

        # Document info
        info_data = [
            ["Document ID:", report.document_id],
            ["Report Date:", report.created_at.strftime("%Y-%m-%d %H:%M:%S")],
            [
                "Overall Status:",
                "✓ PASS" if report.overall_status == "pass" else "✗ FAIL",
            ],
        ]
        info_table = Table(info_data, colWidths=[4 * cm, 10 * cm])
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    (
                        "TEXTCOLOR",
                        (1, 2),
                        (1, 2),
                        colors.green if report.overall_status == "pass" else colors.red,
                    ),
                    ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
                ]
            )
        )
        elements.append(info_table)
        elements.append(Spacer(1, 0.5 * cm))

        # Status summary box
        if report.overall_status == "pass":
            status_box = Table(
                [["✓ 检查通过 / Check Passed"]],
                colWidths=[14 * cm],
            )
            status_box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#d4edda")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#155724")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 14),
                        ("PADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )
        else:
            status_box = Table(
                [["✗ 检查未通过 / Check Failed"]],
                colWidths=[14 * cm],
            )
            status_box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8d7da")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#721c24")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 14),
                        ("PADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )
        elements.append(status_box)
        elements.append(Spacer(1, 0.5 * cm))

        # Validation Results
        elements.append(Paragraph("检查结果 / Validation Results", header_style))

        passed_count = sum(1 for v in report.validations if v.passed)
        total_count = len(report.validations)

        elements.append(
            Paragraph(
                f"Passed: {passed_count}/{total_count}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 0.3 * cm))

        # Validation table
        validation_data = [["Field", "Status", "Details"]]
        for validation in report.validations:
            status_text = "✓ Pass" if validation.passed else "✗ Fail"
            error_text = validation.error_message or ""
            validation_data.append(
                [
                    validation.field_name,
                    status_text,
                    error_text,
                ]
            )

        validation_table = Table(
            validation_data,
            colWidths=[5 * cm, 2.5 * cm, 6.5 * cm],
            repeatRows=1,
        )
        validation_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(validation_table)
        elements.append(Spacer(1, 0.5 * cm))

        # Fix Instructions (if failed)
        if report.fix_instructions:
            elements.append(
                Paragraph("修复建议 / Fix Instructions", header_style)
            )
            elements.append(
                Paragraph(
                    "请根据以下建议修正文档问题:",
                    styles["Normal"],
                )
            )
            elements.append(Spacer(1, 0.2 * cm))

            for instruction in report.fix_instructions:
                elements.append(
                    Paragraph(
                        f"• {instruction}",
                        styles["Normal"],
                    )
                )
            elements.append(Spacer(1, 0.5 * cm))

        # Extracted Fields Summary
        elements.append(
            Paragraph("提取字段摘要 / Extracted Fields Summary", header_style)
        )

        if report.extracted_fields:
            # Filter out internal fields
            display_fields = [
                f for f in report.extracted_fields if not f.name.startswith("_")
            ]

            fields_data = [["Field Name", "Value", "Confidence"]]
            for field in display_fields[:20]:  # Limit to first 20 fields
                fields_data.append(
                    [
                        field.name,
                        field.value[:50],  # Truncate long values
                        f"{field.confidence:.0%}",
                    ]
                )

            fields_table = Table(
                fields_data,
                colWidths=[4 * cm, 8 * cm, 2 * cm],
                repeatRows=1,
            )
            fields_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27ae60")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ]
                )
            )
            elements.append(fields_table)

        # Footer
        elements.append(Spacer(1, 1 * cm))
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=1,  # Center
        )
        elements.append(
            Paragraph(
                "Generated by Shipper Lite | Document Compliance Checker",
                footer_style,
            )
        )

        # Build PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        return pdf
