"""
Pydantic models for Invoice API
Defines request and response schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class InvoiceUploadResponse(BaseModel):
    """Response model for successful invoice upload"""
    invoice_id: int = Field(..., description="Generated invoice ID from database")
    invoice_number: str = Field(..., description="Extracted invoice number")
    vendor_name: str = Field(..., description="Extracted vendor name")
    file_name: str = Field(..., description="Original PDF file name")
    file_size_kb: float = Field(..., description="File size in kilobytes")
    confidence_score: float = Field(..., description="Average extraction confidence (0-1)")
    status: str = Field(default="PROCESSED", description="Processing status")
    message: str = Field(default="Invoice processed successfully", description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_id": 123,
                "invoice_number": "INV-2024-001",
                "vendor_name": "ABC Corporation Inc.",
                "file_name": "invoice_january.pdf",
                "file_size_kb": 245.6,
                "confidence_score": 0.95,
                "status": "PROCESSED",
                "message": "Invoice processed successfully",
                "timestamp": "2024-01-13T10:30:00"
            }
        }


class InvoiceDetail(BaseModel):
    """Detailed invoice model for GET requests"""
    invoice_id: int
    invoice_number: str
    vendor_name: str
    upload_timestamp: Optional[str] = None
    file_name: Optional[str] = None
    file_size_kb: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_id": 123,
                "invoice_number": "INV-2024-001",
                "vendor_name": "ABC Corporation Inc.",
                "upload_timestamp": "2024-01-13T10:30:00",
                "file_name": "invoice_january.pdf",
                "file_size_kb": 245.6,
                "status": "PROCESSED",
                "error_message": None,
                "created_at": "2024-01-13T10:30:00"
            }
        }


class InvoiceListResponse(BaseModel):
    """Response model for invoice list"""
    invoices: List[InvoiceDetail]
    total: int = Field(..., description="Total number of invoices")
    limit: int = Field(..., description="Number of records per page")
    offset: int = Field(..., description="Offset for pagination")

    class Config:
        json_schema_extra = {
            "example": {
                "invoices": [
                    {
                        "invoice_id": 123,
                        "invoice_number": "INV-2024-001",
                        "vendor_name": "ABC Corporation",
                        "upload_timestamp": "2024-01-13T10:30:00",
                        "file_name": "invoice_january.pdf",
                        "file_size_kb": 245.6,
                        "status": "PROCESSED",
                        "created_at": "2024-01-13T10:30:00"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type or code")
    detail: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "detail": "Invalid file type. Only PDF files are allowed.",
                "timestamp": "2024-01-13T10:30:00"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    database_connected: bool = Field(..., description="Database connectivity status")
    document_ai_configured: bool = Field(..., description="Document AI configuration status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "All systems operational",
                "database_connected": True,
                "document_ai_configured": True,
                "timestamp": "2024-01-13T10:30:00"
            }
        }
