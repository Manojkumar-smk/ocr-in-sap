"""
SAP Document Information Extraction Service
Handles invoice PDF upload and data extraction using SAP Document AI
"""

import httpx
import asyncio
import json
from typing import Dict, Optional, Tuple
from pathlib import Path
from app.config import get_dox_config
from app.services.uaa_service import get_uaa_service


class DocumentAIService:
    """
    Service for interacting with SAP Document Information Extraction API
    Handles document upload, polling, and field extraction
    """

    def __init__(self):
        self.dox_config = get_dox_config()
        self.uaa_service = get_uaa_service()
        self.max_poll_attempts = 30  # 30 attempts * 2 seconds = 60 seconds max
        self.poll_interval = 2  # seconds

    async def extract_invoice_data(self, pdf_file_path: str) -> Dict:
        """
        Extract invoice number and vendor name from PDF using Document AI

        Args:
            pdf_file_path: Path to the PDF file

        Returns:
            dict: Extracted data with invoice_number, vendor_name, confidence_score, raw_json

        Raises:
            Exception: If extraction fails at any step
        """
        # Step 1: Get OAuth token
        access_token = await self.uaa_service.get_access_token()

        # Step 2: Upload document
        document_id = await self._upload_document(pdf_file_path, access_token)

        # Step 3: Poll for results
        extraction_result = await self._poll_for_results(document_id, access_token)

        # Step 4: Parse extraction results
        parsed_data = self._parse_extraction_results(extraction_result)

        return parsed_data

    async def _upload_document(self, pdf_file_path: str, access_token: str) -> str:
        """
        Upload PDF document to Document AI

        Returns:
            str: Document ID for polling
        """
        upload_url = f"{self.dox_config.document_ai_url}{self.dox_config.document_ai_api_path}document/jobs"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # Prepare file for upload
        with open(pdf_file_path, 'rb') as pdf_file:
            files = {
                "file": (Path(pdf_file_path).name, pdf_file, "application/pdf")
            }

            # Document AI options
            options = {
                "extraction": {
                    "headerFields": [
                        "invoiceNumber",
                        "purchaseOrderNumber",
                        "invoiceDate",
                        "currency",
                        "grossAmount",
                        "netAmount",
                        "senderName",
                        "senderAddress",
                        "receiverName"
                    ],
                    "lineItemFields": []
                },
                "schemaName": "SAP_invoice_schema",
                "clientId": "default",
                "documentType": "invoice",
                "receivedDate": ""
            }

            data = {
                "options": json.dumps(options)
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    upload_url,
                    headers=headers,
                    files=files,
                    data=data
                )

                if response.status_code not in [200, 201]:
                    raise Exception(
                        f"Document upload failed: {response.status_code} - {response.text}"
                    )

                response_data = response.json()
                document_id = response_data.get("id")

                if not document_id:
                    raise Exception("No document ID returned from upload")

                return document_id

    async def _poll_for_results(self, document_id: str, access_token: str) -> Dict:
        """
        Poll Document AI for extraction results

        Returns:
            dict: Complete extraction results
        """
        poll_url = f"{self.dox_config.document_ai_url}{self.dox_config.document_ai_api_path}document/jobs/{document_id}"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        for attempt in range(self.max_poll_attempts):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(poll_url, headers=headers)

                if response.status_code != 200:
                    raise Exception(
                        f"Polling failed: {response.status_code} - {response.text}"
                    )

                result = response.json()
                status = result.get("status")

                if status == "DONE":
                    return result
                elif status == "FAILED":
                    raise Exception(f"Document extraction failed: {result.get('error', 'Unknown error')}")
                elif status in ["PENDING", "RUNNING"]:
                    # Continue polling
                    await asyncio.sleep(self.poll_interval)
                else:
                    raise Exception(f"Unknown status: {status}")

        raise Exception(f"Extraction timeout after {self.max_poll_attempts * self.poll_interval} seconds")

    def _parse_extraction_results(self, extraction_result: Dict) -> Dict:
        """
        Parse extraction results to get invoice number and vendor name

        Returns:
            dict: Parsed data with invoice_number, vendor_name, confidence_score, raw_json
        """
        try:
            # Get extraction data
            extraction = extraction_result.get("extraction", {})
            header_fields = extraction.get("headerFields", [])

            # Extract specific fields
            invoice_number = None
            vendor_name = None
            confidence_scores = []

            for field in header_fields:
                field_name = field.get("name", "")
                field_value = field.get("value")
                field_confidence = field.get("confidence", 0)

                if field_confidence:
                    confidence_scores.append(field_confidence)

                # Extract invoice number
                if field_name == "invoiceNumber" and field_value:
                    invoice_number = str(field_value)

                # Extract vendor name (senderName in Document AI)
                if field_name == "senderName" and field_value:
                    vendor_name = str(field_value)

            # Calculate average confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            # Validation
            if not invoice_number:
                raise Exception("Invoice number not found in extraction results")

            if not vendor_name:
                raise Exception("Vendor name not found in extraction results")

            return {
                "invoice_number": invoice_number,
                "vendor_name": vendor_name,
                "confidence_score": round(avg_confidence, 2),
                "raw_json": json.dumps(extraction_result)
            }

        except KeyError as e:
            raise Exception(f"Error parsing extraction results: Missing key {str(e)}")
        except Exception as e:
            raise Exception(f"Error parsing extraction results: {str(e)}")


# Singleton instance
_document_ai_service: Optional[DocumentAIService] = None


def get_document_ai_service() -> DocumentAIService:
    """Get or create Document AI service singleton"""
    global _document_ai_service
    if _document_ai_service is None:
        _document_ai_service = DocumentAIService()
    return _document_ai_service
