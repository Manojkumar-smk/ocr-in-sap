# Invoice OCR System

An enterprise-grade invoice processing system built with SAPUI5, Python FastAPI, SAP Document Information Extraction, and SAP HANA Cloud.

## Overview

This application allows users to upload invoice PDFs through a modern web interface. The system automatically extracts key information (invoice number and vendor name) using SAP Document Information Extraction AI service and stores the data in SAP HANA Cloud database.

### Architecture

```
User → UI5 Frontend → FastAPI Backend → SAP Document AI → HANA Cloud
         ↓               ↓                    ↓               ↓
    File Upload    PDF Processing    AI Extraction    Data Storage
```

## Features

- PDF invoice upload with drag-and-drop support
- Automatic extraction of invoice number and vendor name
- AI-powered OCR using SAP Document Information Extraction
- Persistent storage in SAP HANA Cloud
- Modern, responsive UI built with SAPUI5
- RESTful API with automatic documentation
- OAuth 2.0 authentication with SAP UAA
- Docker support for containerized deployment

## Tech Stack

### Frontend
- **SAPUI5 1.120.0** - Enterprise-ready UI framework
- **OpenUI5 Controls** - sap.m, sap.ui.unified for file upload
- **Responsive Design** - Works on desktop, tablet, and mobile

### Backend
- **Python 3.11** - Modern Python runtime
- **FastAPI** - High-performance async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and settings management
- **httpx** - Async HTTP client for Document AI API

### Services
- **SAP Document Information Extraction** - AI-powered invoice data extraction
- **SAP HANA Cloud** - Enterprise database
- **SAP UAA** - OAuth 2.0 authentication

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- SAP BTP Trial or Enterprise account
- SAP HANA Cloud instance
- SAP Document Information Extraction service instance
- Git

## Project Structure

```
ocr-in-sap/
├── frontend/                   # SAPUI5 Application
│   ├── webapp/
│   │   ├── controller/        # UI controllers
│   │   ├── view/             # XML views
│   │   ├── i18n/             # Internationalization
│   │   ├── css/              # Stylesheets
│   │   ├── Component.js
│   │   ├── manifest.json
│   │   └── index.html
│   ├── package.json
│   └── ui5.yaml
│
├── backend/                    # Python FastAPI Service
│   ├── app/
│   │   ├── services/          # Business logic
│   │   ├── routers/           # API endpoints
│   │   ├── models/            # Pydantic models
│   │   ├── config.py          # Configuration
│   │   └── main.py            # Application entry
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── dox-service-key.json   # Document AI credentials
│
├── db/
│   └── schema/
│       └── invoices.sql       # HANA table definitions
│
├── deployment/
│   └── mta.yaml              # Multi-Target App descriptor
│
├── .gitignore
└── README.md
```

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Manojkumar-smk/ocr-in-sap.git
cd ocr-in-sap
```

### 2. Set Up HANA Cloud Database

1. Log in to SAP BTP Cockpit
2. Create or open your SAP HANA Cloud instance
3. Open HANA Database Explorer
4. Execute the SQL script to create the database schema:

```bash
# Run the schema creation script
cat db/schema/invoices.sql
```

Copy and execute this in HANA Database Explorer.

### 3. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env

# Edit .env file with your HANA credentials
nano .env  # or use your preferred editor
```

Update the `.env` file with your HANA Cloud connection details:

```env
HANA_HOST=your-hana-instance.hanacloud.ondemand.com
HANA_PORT=443
HANA_USER=DBADMIN
HANA_PASSWORD=your-password
```

The `dox-service-key.json` file has already been created with your Document AI credentials.

### 4. Test Backend

```bash
# Test UAA authentication
python -m app.services.uaa_service

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs to see the interactive API documentation.

### 5. Set Up Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Start the UI5 development server
npm start
```

The application will open automatically at http://localhost:8080

### 6. Test the Application

1. Open http://localhost:8080 in your browser
2. Click "Choose PDF file" and select an invoice PDF
3. Click "Upload & Extract"
4. View the extracted invoice number and vendor name

## API Endpoints

### POST /api/v1/invoices/upload
Upload and process invoice PDF

**Request:**
- Content-Type: multipart/form-data
- Body: file (PDF)

**Response:**
```json
{
  "invoice_id": 123,
  "invoice_number": "INV-2024-001",
  "vendor_name": "ABC Corporation Inc.",
  "file_name": "invoice.pdf",
  "file_size_kb": 245.6,
  "confidence_score": 0.95,
  "status": "PROCESSED",
  "message": "Invoice processed successfully",
  "timestamp": "2024-01-13T10:30:00"
}
```

### GET /api/v1/invoices/{invoice_id}
Get invoice by ID

### GET /api/v1/invoices
List all invoices with pagination

Query parameters:
- `limit` (int): Number of records (default: 50, max: 100)
- `offset` (int): Records to skip (default: 0)

### GET /api/v1/health
Service health check

Returns status of database connectivity and Document AI configuration.

## SAP Document Information Extraction

The application uses SAP Document Information Extraction service to extract invoice data. The service:

- Authenticates using OAuth 2.0 (client credentials flow)
- Uploads PDFs to the Document AI API
- Polls for extraction results (async processing)
- Extracts headerFields: invoiceNumber, senderName
- Returns confidence scores for each field

### Extracted Fields

- **Invoice Number**: Extracted from headerFields.invoiceNumber
- **Vendor Name**: Extracted from headerFields.senderName

## Database Schema

```sql
CREATE COLUMN TABLE INVOICES (
    INVOICE_ID BIGINT PRIMARY KEY,
    INVOICE_NUMBER NVARCHAR(100) NOT NULL,
    VENDOR_NAME NVARCHAR(500) NOT NULL,
    UPLOAD_TIMESTAMP TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FILE_NAME NVARCHAR(500),
    FILE_SIZE_KB DECIMAL(10,2),
    RAW_TEXT NCLOB,
    STATUS NVARCHAR(50) DEFAULT 'PROCESSED',
    ERROR_MESSAGE NVARCHAR(2000),
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Deployment to SAP BTP

### Prerequisites
- Cloud Foundry CLI installed
- MBT (Multi-Target Application) build tool installed
- Logged in to SAP BTP: `cf login`

### Build and Deploy

```bash
# Build MTA archive
cd deployment
mbt build

# Deploy to SAP BTP
cf deploy mta_archives/invoice-ocr-system_1.0.0.mtar

# Check deployment status
cf apps
cf services
```

### Post-Deployment

1. Get application URL: `cf app invoice-ocr-backend`
2. Update frontend manifest.json with production API URL
3. Test the deployed application

## Configuration

### Backend Configuration

Environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| HANA_HOST | HANA Cloud hostname | - |
| HANA_PORT | HANA Cloud port | 443 |
| HANA_USER | Database user | DBADMIN |
| HANA_PASSWORD | Database password | - |
| MAX_FILE_SIZE_MB | Max upload size | 10 |
| UPLOAD_DIR | Temp upload directory | /tmp/uploads |
| CORS_ORIGINS | Allowed CORS origins | ["*"] |

### Frontend Configuration

Update `manifest.json` dataSources for production:

```json
{
  "invoiceAPI": {
    "uri": "https://your-backend-url.cfapps.us10.hana.ondemand.com/api/v1/",
    "type": "JSON"
  }
}
```

## Troubleshooting

### Backend Issues

**UAA Authentication Failed**
- Verify dox-service-key.json is present and valid
- Check network connectivity to UAA endpoint
- Test authentication: `python -m app.services.uaa_service`

**Database Connection Failed**
- Verify HANA Cloud instance is running
- Check .env credentials are correct
- Ensure your IP is whitelisted in HANA Cloud

**Document AI Upload Failed**
- Check file size (max 10MB)
- Ensure PDF is not corrupted
- Verify Document AI service is active in BTP

### Frontend Issues

**CORS Errors**
- Update CORS_ORIGINS in backend .env
- Add frontend URL to allowed origins

**Upload Button Not Working**
- Check browser console for errors
- Verify backend is running on correct port
- Check manifest.json has correct API URL

## Security Considerations

- Never commit `.env` files or `dox-service-key.json`
- Use SAP BTP Credential Store for production secrets
- Enable XSUAA authentication for production deployment
- Implement rate limiting for upload endpoint
- Validate file types and sizes server-side
- Use parameterized SQL queries (already implemented)

## Performance

- **Token Caching**: UAA tokens cached for 12 hours
- **Async Processing**: FastAPI async endpoints for concurrent requests
- **Connection Pooling**: HANA connection reuse
- **Smart Polling**: Exponential backoff for Document AI polling

## Future Enhancements

- Extract additional invoice fields (date, amount, tax, line items)
- Batch upload for multiple invoices
- Manual correction UI for extracted data
- Export to Excel/CSV
- Integration with SAP S/4HANA
- Advanced search and filtering
- Document storage in SAP Document Management Service
- Approval workflow for invoices

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Create a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/Manojkumar-smk/ocr-in-sap/issues
- SAP Community: https://community.sap.com

## Acknowledgments

- SAP Document Information Extraction team
- OpenUI5 / SAPUI5 community
- FastAPI framework
- SAP BTP platform

---

Built with SAP technologies for enterprise invoice processing.
