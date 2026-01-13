"""
SAP UAA Authentication Service
Handles OAuth 2.0 client credentials flow for SAP Document Information Extraction
"""

import httpx
import time
from typing import Optional
from app.config import get_dox_config


class UAAService:
    """
    Service for OAuth authentication with SAP UAA
    Implements token caching to minimize auth requests
    """

    def __init__(self):
        self.dox_config = get_dox_config()
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def get_access_token(self) -> str:
        """
        Get OAuth access token for Document AI API
        Returns cached token if still valid, otherwise requests new token

        Returns:
            str: Bearer access token

        Raises:
            HTTPError: If authentication fails
        """
        # Return cached token if still valid (with 5 minute buffer)
        if self._cached_token and time.time() < (self._token_expires_at - 300):
            return self._cached_token

        # Request new token
        token_url = f"{self.dox_config.uaa_url}/oauth/token"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials",
            "client_id": self.dox_config.uaa_client_id,
            "client_secret": self.dox_config.uaa_client_secret
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                headers=headers,
                data=data,
                timeout=30.0
            )

            if response.status_code != 200:
                raise httpx.HTTPError(
                    f"UAA authentication failed: {response.status_code} - {response.text}"
                )

            token_data = response.json()
            self._cached_token = token_data["access_token"]

            # Calculate expiration time (default 12 hours if not provided)
            expires_in = token_data.get("expires_in", 43200)  # 12 hours default
            self._token_expires_at = time.time() + expires_in

            return self._cached_token

    def clear_cache(self):
        """Clear cached token (useful for testing or forcing re-authentication)"""
        self._cached_token = None
        self._token_expires_at = 0


# Singleton instance
_uaa_service: Optional[UAAService] = None


def get_uaa_service() -> UAAService:
    """Get or create UAA service singleton"""
    global _uaa_service
    if _uaa_service is None:
        _uaa_service = UAAService()
    return _uaa_service


# For standalone testing
async def main():
    """Test UAA authentication"""
    service = get_uaa_service()
    try:
        token = await service.get_access_token()
        print(f"Successfully obtained access token")
        print(f"Token (first 50 chars): {token[:50]}...")
        print(f"Token expires at: {service._token_expires_at}")
    except Exception as e:
        print(f"Authentication failed: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
