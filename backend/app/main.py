"""
Invoice OCR Backend - Main Application
FastAPI application entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings, get_dox_config
from app.routers import invoice_router
from app.services.database_service import get_database_service
from app.services.uaa_service import get_uaa_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    Runs on startup and shutdown
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.API_VERSION}")

    # Validate Document AI configuration
    try:
        dox_config = get_dox_config()
        print(f"✓ Document AI configured: {dox_config.document_ai_url}")
    except Exception as e:
        print(f"✗ Document AI configuration error: {str(e)}")

    # Test database connection
    try:
        db_service = get_database_service()
        db_connected = db_service.test_connection()
        if db_connected:
            print(f"✓ Database connected: {settings.HANA_HOST}")
        else:
            print(f"✗ Database connection failed")
    except Exception as e:
        print(f"✗ Database error: {str(e)}")

    # Test UAA authentication
    try:
        uaa_service = get_uaa_service()
        token = await uaa_service.get_access_token()
        print(f"✓ UAA authentication successful")
    except Exception as e:
        print(f"✗ UAA authentication error: {str(e)}")

    print(f"{settings.APP_NAME} started successfully")

    yield

    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="Invoice OCR service using SAP Document Information Extraction and HANA Cloud",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(invoice_router.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors
    """
    print(f"Unhandled exception: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected error occurred. Please try again later.",
            "path": str(request.url)
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "documentation": "/docs",
        "health_check": "/api/v1/health"
    }


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
