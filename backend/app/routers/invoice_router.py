"""
Invoice API Router
Handles all invoice-related endpoints
"""

import os
import aiofiles
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.invoice import (
    InvoiceUploadResponse,
    InvoiceDetail,
    InvoiceListResponse,
    ErrorResponse,
    HealthCheckResponse
)
from app.services.document_ai_service import get_document_ai_service
from app.services.database_service import get_database_service
from app.config import settings, get_dox_config

router = APIRouter(prefix="/api/v1", tags=["invoices"])


@router.post("/invoices/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(..., description="Invoice PDF file")
):
    """
    Upload and process invoice PDF

    - Validates file type and size
    - Extracts invoice number and vendor name using SAP Document AI
    - Stores data in HANA database
    - Returns extracted information
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed."
        )

    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"{timestamp}_{file.filename}"
    temp_filepath = upload_dir / temp_filename

    try:
        # Save uploaded file temporarily
        async with aiofiles.open(temp_filepath, 'wb') as out_file:
            content = await file.read()

            # Check file size (in bytes)
            file_size_bytes = len(content)
            file_size_kb = file_size_bytes / 1024
            max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

            if file_size_bytes > max_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
                )

            await out_file.write(content)

        # Extract data using Document AI
        doc_ai_service = get_document_ai_service()
        extraction_result = await doc_ai_service.extract_invoice_data(str(temp_filepath))

        # Store in database
        db_service = get_database_service()
        invoice_id = db_service.insert_invoice(
            invoice_number=extraction_result["invoice_number"],
            vendor_name=extraction_result["vendor_name"],
            file_name=file.filename,
            file_size_kb=file_size_kb,
            raw_text=extraction_result["raw_json"],
            status="PROCESSED"
        )

        # Prepare response
        return InvoiceUploadResponse(
            invoice_id=invoice_id,
            invoice_number=extraction_result["invoice_number"],
            vendor_name=extraction_result["vendor_name"],
            file_name=file.filename,
            file_size_kb=round(file_size_kb, 2),
            confidence_score=extraction_result["confidence_score"],
            status="PROCESSED",
            message="Invoice processed successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log error and save failed record
        error_message = str(e)

        try:
            db_service = get_database_service()
            db_service.insert_invoice(
                invoice_number="UNKNOWN",
                vendor_name="UNKNOWN",
                file_name=file.filename,
                file_size_kb=file_size_kb if 'file_size_kb' in locals() else 0,
                raw_text="",
                status="FAILED",
                error_message=error_message
            )
        except:
            pass  # If DB insert fails, just continue with error response

        raise HTTPException(
            status_code=422,
            detail=f"Failed to process invoice: {error_message}"
        )

    finally:
        # Clean up temporary file
        if temp_filepath.exists():
            try:
                os.remove(temp_filepath)
            except:
                pass  # Ignore cleanup errors


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetail)
async def get_invoice(invoice_id: int):
    """
    Get invoice by ID

    Returns detailed information about a specific invoice
    """
    db_service = get_database_service()
    invoice = db_service.get_invoice(invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice with ID {invoice_id} not found"
        )

    return InvoiceDetail(**invoice)


@router.get("/invoices", response_model=InvoiceListResponse)
async def get_all_invoices(
    limit: int = Query(default=50, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip")
):
    """
    Get all invoices with pagination

    Returns a list of invoices sorted by upload timestamp (newest first)
    """
    db_service = get_database_service()
    invoices = db_service.get_all_invoices(limit=limit, offset=offset)

    # Convert to InvoiceDetail models
    invoice_details = [InvoiceDetail(**inv) for inv in invoices]

    return InvoiceListResponse(
        invoices=invoice_details,
        total=len(invoice_details),
        limit=limit,
        offset=offset
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint

    Verifies:
    - Service is running
    - Database connectivity
    - Document AI configuration
    """
    database_connected = False
    document_ai_configured = False

    # Test database connection
    try:
        db_service = get_database_service()
        database_connected = db_service.test_connection()
    except Exception as e:
        print(f"Database health check failed: {str(e)}")

    # Test Document AI configuration
    try:
        dox_config = get_dox_config()
        document_ai_configured = bool(dox_config.uaa_url and dox_config.document_ai_url)
    except Exception as e:
        print(f"Document AI config check failed: {str(e)}")

    # Determine overall status
    if database_connected and document_ai_configured:
        status = "healthy"
        message = "All systems operational"
    else:
        status = "degraded"
        issues = []
        if not database_connected:
            issues.append("database")
        if not document_ai_configured:
            issues.append("document_ai")
        message = f"Issues detected: {', '.join(issues)}"

    return HealthCheckResponse(
        status=status,
        message=message,
        database_connected=database_connected,
        document_ai_configured=document_ai_configured
    )
