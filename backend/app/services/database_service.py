"""
SAP HANA Database Service
Handles all database operations for invoice storage and retrieval
"""

from typing import Dict, List, Optional
from contextlib import contextmanager
from hdbcli import dbapi
from app.config import settings


class DatabaseService:
    """
    Service for SAP HANA database operations
    Uses context manager for connection handling
    """

    def __init__(self):
        self.host = settings.HANA_HOST
        self.port = settings.HANA_PORT
        self.user = settings.HANA_USER
        self.password = settings.HANA_PASSWORD
        self.encrypt = settings.HANA_ENCRYPT

    @contextmanager
    def get_connection(self):
        """
        Context manager for HANA database connection
        Automatically commits on success, rolls back on error
        """
        connection = None
        try:
            connection = dbapi.connect(
                address=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                encrypt=self.encrypt,
                sslValidateCertificate=False  # For BTP Cloud
            )
            yield connection
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.close()

    def insert_invoice(
        self,
        invoice_number: str,
        vendor_name: str,
        file_name: str,
        file_size_kb: float,
        raw_text: str,
        status: str = "PROCESSED",
        error_message: Optional[str] = None
    ) -> int:
        """
        Insert invoice record into database

        Args:
            invoice_number: Extracted invoice number
            vendor_name: Extracted vendor name
            file_name: Original PDF file name
            file_size_kb: File size in kilobytes
            raw_text: Raw JSON extraction results
            status: Processing status (default: PROCESSED)
            error_message: Error message if processing failed

        Returns:
            int: Generated INVOICE_ID

        Raises:
            Exception: If database operation fails
        """
        insert_query = """
            INSERT INTO INVOICES (
                INVOICE_NUMBER,
                VENDOR_NAME,
                FILE_NAME,
                FILE_SIZE_KB,
                RAW_TEXT,
                STATUS,
                ERROR_MESSAGE
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                insert_query,
                (invoice_number, vendor_name, file_name, file_size_kb, raw_text, status, error_message)
            )

            # Get the generated ID
            cursor.execute("SELECT CURRENT_IDENTITY_VALUE() FROM DUMMY")
            invoice_id = cursor.fetchone()[0]
            cursor.close()

            return invoice_id

    def get_invoice(self, invoice_id: int) -> Optional[Dict]:
        """
        Get invoice by ID

        Args:
            invoice_id: Invoice ID to retrieve

        Returns:
            dict: Invoice data or None if not found
        """
        select_query = """
            SELECT
                INVOICE_ID,
                INVOICE_NUMBER,
                VENDOR_NAME,
                UPLOAD_TIMESTAMP,
                FILE_NAME,
                FILE_SIZE_KB,
                STATUS,
                ERROR_MESSAGE,
                CREATED_AT
            FROM INVOICES
            WHERE INVOICE_ID = ?
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(select_query, (invoice_id,))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                "invoice_id": row[0],
                "invoice_number": row[1],
                "vendor_name": row[2],
                "upload_timestamp": row[3].isoformat() if row[3] else None,
                "file_name": row[4],
                "file_size_kb": float(row[5]) if row[5] else None,
                "status": row[6],
                "error_message": row[7],
                "created_at": row[8].isoformat() if row[8] else None
            }

    def get_all_invoices(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Get all invoices with pagination

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            list: List of invoice records
        """
        select_query = """
            SELECT
                INVOICE_ID,
                INVOICE_NUMBER,
                VENDOR_NAME,
                UPLOAD_TIMESTAMP,
                FILE_NAME,
                FILE_SIZE_KB,
                STATUS,
                CREATED_AT
            FROM INVOICES
            ORDER BY UPLOAD_TIMESTAMP DESC
            LIMIT ? OFFSET ?
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(select_query, (limit, offset))
            rows = cursor.fetchall()
            cursor.close()

            invoices = []
            for row in rows:
                invoices.append({
                    "invoice_id": row[0],
                    "invoice_number": row[1],
                    "vendor_name": row[2],
                    "upload_timestamp": row[3].isoformat() if row[3] else None,
                    "file_name": row[4],
                    "file_size_kb": float(row[5]) if row[5] else None,
                    "status": row[6],
                    "created_at": row[7].isoformat() if row[7] else None
                })

            return invoices

    def test_connection(self) -> bool:
        """
        Test database connectivity

        Returns:
            bool: True if connection successful

        Raises:
            Exception: If connection fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUMMY")
            result = cursor.fetchone()
            cursor.close()
            return result[0] == 1


# Singleton instance
_database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get or create Database service singleton"""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
