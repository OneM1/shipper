"""API routes."""
import uuid
from typing import Dict

from fastapi import APIRouter, UploadFile, File, HTTPException, Response

from app.models.schemas import (
    ComplianceReport,
    DocumentUploadResponse,
    ProcessingStatus,
)
from app.services.document_parser import DocumentParser
from app.services.validation_engine import ValidationEngine
from app.services.report_generator import ReportGenerator
from app.services.pdf_generator import PDFReportGenerator

router = APIRouter()

# In-memory storage for demo (replace with database in production)
document_store: Dict[str, dict] = {}

# Service instances
document_parser = DocumentParser()
validation_engine = ValidationEngine()
report_generator = ReportGenerator()
pdf_generator = PDFReportGenerator()


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    invoice: UploadFile = File(...),
    packing_list: UploadFile = File(...),
) -> DocumentUploadResponse:
    """Upload invoice and packing list for compliance check."""
    # Generate document ID
    document_id = str(uuid.uuid4())
    
    # Validate file types
    allowed_types = ["application/pdf", "image/png", "image/jpeg"]
    
    if invoice.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid invoice file type. Allowed: PDF, PNG, JPG"
        )
    
    if packing_list.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid packing list file type. Allowed: PDF, PNG, JPG"
        )
    
    # Store document info
    document_store[document_id] = {
        "status": ProcessingStatus.PROCESSING,
        "invoice_filename": invoice.filename,
        "packing_list_filename": packing_list.filename,
        "invoice_file": invoice.file,
        "packing_list_file": packing_list.file,
    }
    
    # Process documents immediately (in production, use background tasks)
    try:
        # Parse invoice
        invoice.file.seek(0)
        invoice_fields = await document_parser.parse_document(
            invoice.file, "invoice"
        )
        
        # Parse packing list
        packing_list.file.seek(0)
        packing_list_fields = await document_parser.parse_document(
            packing_list.file, "packing_list"
        )
        
        # Validate invoice fields
        invoice_validations = validation_engine.validate(invoice_fields)
        
        # Validate packing list fields
        packing_validations = validation_engine.validate(packing_list_fields)
        
        # Cross-document validation
        cross_validations = validation_engine.validate_cross_document(
            invoice_fields, packing_list_fields
        )
        
        # Combine all validations
        all_validations = invoice_validations + packing_validations + cross_validations
        
        # Combine all fields
        all_fields = invoice_fields + packing_list_fields
        
        # Generate report
        report = report_generator.generate(
            document_id=document_id,
            extracted_fields=all_fields,
            validations=all_validations,
        )
        
        # Store results
        document_store[document_id].update({
            "status": ProcessingStatus.COMPLETED,
            "report": report,
            "invoice_fields": invoice_fields,
            "packing_list_fields": packing_list_fields,
        })
        
        return DocumentUploadResponse(
            document_id=document_id,
            status=ProcessingStatus.COMPLETED,
            message="Documents processed successfully"
        )
        
    except Exception as e:
        document_store[document_id]["status"] = ProcessingStatus.FAILED
        document_store[document_id]["error"] = str(e)
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(e)}"
        )


@router.get("/documents/{document_id}/status")
async def get_document_status(document_id: str) -> dict:
    """Get processing status of uploaded documents."""
    if document_id not in document_store:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    doc = document_store[document_id]
    return {
        "document_id": document_id,
        "status": doc["status"],
        "invoice_filename": doc.get("invoice_filename"),
        "packing_list_filename": doc.get("packing_list_filename"),
    }


@router.get("/documents/{document_id}/report", response_model=ComplianceReport)
async def get_compliance_report(document_id: str) -> ComplianceReport:
    """Get compliance report for processed documents."""
    if document_id not in document_store:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    doc = document_store[document_id]
    
    if doc["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document processing not completed. Current status: {doc['status']}"
        )
    
    report = doc.get("report")
    if not report:
        raise HTTPException(
            status_code=500,
            detail="Report not found"
        )
    
    return report


@router.get("/documents/{document_id}/fields")
async def get_extracted_fields(document_id: str) -> dict:
    """Get extracted fields from documents (for debugging)."""
    if document_id not in document_store:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    doc = document_store[document_id]
    
    return {
        "document_id": document_id,
        "status": doc["status"],
        "invoice_fields": [
            {"name": f.name, "value": f.value, "confidence": f.confidence}
            for f in doc.get("invoice_fields", [])
            if not f.name.startswith("_")
        ],
        "packing_list_fields": [
            {"name": f.name, "value": f.value, "confidence": f.confidence}
            for f in doc.get("packing_list_fields", [])
            if not f.name.startswith("_")
        ],
    }


@router.get("/documents/{document_id}/debug")
async def debug_document(document_id: str) -> dict:
    """Debug endpoint - shows raw extraction results."""
    if document_id not in document_store:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    doc = document_store[document_id]
    
    # Check for errors
    invoice_errors = [f for f in doc.get("invoice_fields", []) if f.name.startswith("_error")]
    packing_errors = [f for f in doc.get("packing_list_fields", []) if f.name.startswith("_error")]
    
    invoice_fields = [
        {"name": f.name, "value": f.value, "confidence": f.confidence}
        for f in doc.get("invoice_fields", [])
    ]
    
    packing_list_fields = [
        {"name": f.name, "value": f.value, "confidence": f.confidence}
        for f in doc.get("packing_list_fields", [])
    ]
    
    # Get validation results
    report = doc.get("report")
    validations = []
    if report:
        validations = [
            {"field": v.field_name, "passed": v.passed, "error": v.error_message}
            for v in report.validations
        ]
    
    return {
        "document_id": document_id,
        "status": doc["status"],
        "invoice_filename": doc.get("invoice_filename"),
        "packing_list_filename": doc.get("packing_list_filename"),
        "invoice_errors": [e.value for e in invoice_errors],
        "packing_list_errors": [e.value for e in packing_errors],
        "invoice_fields": invoice_fields,
        "packing_list_fields": packing_list_fields,
        "validations": validations,
        "overall_status": report.overall_status if report else "unknown",
        "fix_instructions": report.fix_instructions if report else [],
    }


@router.get("/documents/{document_id}/report.pdf")
async def download_pdf_report(document_id: str) -> Response:
    """Download compliance report as PDF."""
    if document_id not in document_store:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    doc = document_store[document_id]
    
    if doc["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document processing not completed. Current status: {doc['status']}"
        )
    
    report = doc.get("report")
    if not report:
        raise HTTPException(
            status_code=500,
            detail="Report not found"
        )
    
    # Generate PDF
    try:
        pdf_bytes = pdf_generator.generate(report)
        
        # Create response with PDF content
        headers = {
            "Content-Disposition": f"attachment; filename=shipper_report_{document_id[:8]}.pdf"
        }
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )
