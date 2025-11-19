"""Jamf Pro API client.

This module implements a minimal Jamf Pro API client using the modern
bearer-token-based authentication flow (/api/v1/auth/token).

It is intentionally small and focused on the endpoints needed by the
Gemini Endpoint Advisor CLI.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests


class JamfClient:
    """Simple Jamf Pro API client.

    Expects the following environment variables to be set:

    - JAMF_BASE_URL
    - JAMF_CLIENT_ID
    - JAMF_CLIENT_SECRET
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.base_url = (base_url or os.environ.get("JAMF_BASE_URL", "")).rstrip("/")
        self.client_id = client_id or os.environ.get("JAMF_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("JAMF_CLIENT_SECRET", "")
        self.timeout = timeout

        if not self.base_url:
            raise ValueError("JAMF_BASE_URL is not set")
        if not self.client_id or not self.client_secret:
            raise ValueError("JAMF_CLIENT_ID and JAMF_CLIENT_SECRET must be set")

        self._token: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------------------ #
    def _get_token(self) -> str:
        if self._token:
            return self._token

        url = f"{self.base_url}/api/v1/auth/token"
        resp = requests.post(
            url,
            auth=(self.client_id, self.client_secret),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("token")
        if not token:
            raise RuntimeError("No token returned from Jamf auth endpoint")
        self._token = token
        return token

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------ #
    # Inventory
    # ------------------------------------------------------------------ #
    def get_computers_inventory(
        self,
        page_size: int = 50,
        max_devices: int = 200,
    ) -> List[Dict[str, Any]]:
        """Fetch a subset of computers via Jamf Pro API /computers-inventory.

        This method paginates until either `max_devices` is reached or there
        are no more devices to fetch.
        """
        url = f"{self.base_url}/api/v1/computers-inventory"
        page = 0
        results: List[Dict[str, Any]] = []

        while len(results) < max_devices:
            params = {
                "page": page,
                "page-size": page_size,
                # Only request the sections we actually use.
                "section": "GENERAL,SECURITY,OPERATING_SYSTEM",
            }
            resp = requests.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self.timeout,
            )
            if resp.status_code == 401:
                # Token may be expired; clear and retry once.
                self._token = None
                resp = requests.get(
                    url,
                    headers=self._headers(),
                    params=params,
                    timeout=self.timeout,
                )

            resp.raise_for_status()
            data = resp.json()
            batch = data.get("results", [])
            if not batch:
                break

            results.extend(batch)
            if len(batch) < page_size:
                # Last page
                break

            page += 1

        return results[:max_devices]
