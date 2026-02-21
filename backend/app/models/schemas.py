"""Pydantic schemas for API requests/responses."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Document types supported for upload."""
    INVOICE = "invoice"
    PACKING_LIST = "packing_list"


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationResult(BaseModel):
    """Individual field validation result."""
    field_name: str
    passed: bool
    error_message: Optional[str] = None
    field_location: Optional[str] = None  # Page/coordinates in document


class ExtractedField(BaseModel):
    """Extracted field from document."""
    name: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class ComplianceReport(BaseModel):
    """Full compliance report response."""
    document_id: str
    overall_status: str  # pass / fail
    created_at: datetime
    extracted_fields: List[ExtractedField]
    validations: List[ValidationResult]
    fix_instructions: List[str]


class DocumentUploadResponse(BaseModel):
    """Document upload response."""
    document_id: str
    status: ProcessingStatus
    message: str
