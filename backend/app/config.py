"""
Configuration management for Invoice OCR Backend
Loads settings from environment variables and SAP Document AI service key
"""

import json
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables and service key"""

    # Application Settings
    APP_NAME: str = "Invoice OCR Service"
    API_VERSION: str = "v1"
    DEBUG: bool = False

    # SAP HANA Database Settings
    HANA_HOST: str = Field(default="", description="HANA Cloud host")
    HANA_PORT: int = Field(default=443, description="HANA Cloud port")
    HANA_USER: str = Field(default="", description="HANA database user")
    HANA_PASSWORD: str = Field(default="", description="HANA database password")
    HANA_SCHEMA: Optional[str] = Field(default=None, description="HANA schema name")
    HANA_ENCRYPT: bool = Field(default=True, description="Use SSL/TLS encryption")

    # File Upload Settings
    MAX_FILE_SIZE_MB: int = Field(default=10, description="Max PDF file size in MB")
    ALLOWED_EXTENSIONS: list = Field(default=[".pdf"], description="Allowed file extensions")
    UPLOAD_DIR: str = Field(default="/tmp/uploads", description="Temporary upload directory")

    # CORS Settings
    CORS_ORIGINS: list = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    # SAP Document Information Extraction (loaded from service key)
    DOX_SERVICE_KEY_PATH: str = Field(
        default="dox-service-key.json",
        description="Path to Document AI service key file"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


class DocumentAIConfig:
    """
    Configuration for SAP Document Information Extraction service
    Loaded from service key JSON file
    """

    def __init__(self, service_key_path: str = "dox-service-key.json"):
        self.service_key_path = service_key_path
        self._service_key = None
        self._load_service_key()

    def _load_service_key(self):
        """Load service key from JSON file"""
        # Try multiple paths
        possible_paths = [
            self.service_key_path,
            os.path.join("backend", self.service_key_path),
            os.path.join(os.path.dirname(__file__), "..", self.service_key_path),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self._service_key = json.load(f)
                    print(f"Loaded Document AI service key from: {path}")
                    return

        raise FileNotFoundError(
            f"Could not find service key file. Tried paths: {possible_paths}"
        )

    @property
    def uaa_url(self) -> str:
        """Get UAA authentication URL"""
        return self._service_key["uaa"]["url"]

    @property
    def uaa_client_id(self) -> str:
        """Get UAA client ID"""
        return self._service_key["uaa"]["clientid"]

    @property
    def uaa_client_secret(self) -> str:
        """Get UAA client secret"""
        return self._service_key["uaa"]["clientsecret"]

    @property
    def document_ai_url(self) -> str:
        """Get Document AI base URL"""
        return self._service_key["url"]

    @property
    def document_ai_api_path(self) -> str:
        """Get Document AI REST API path"""
        return self._service_key["resturl"]

    @property
    def full_api_url(self) -> str:
        """Get full Document AI API URL"""
        return f"{self.document_ai_url}{self.document_ai_api_path}"


# Singleton instances
settings = Settings()
dox_config = None

def get_dox_config() -> DocumentAIConfig:
    """Get or create Document AI configuration singleton"""
    global dox_config
    if dox_config is None:
        dox_config = DocumentAIConfig(settings.DOX_SERVICE_KEY_PATH)
    return dox_config
