
from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import httpx


class MiroFishConnectionError(RuntimeError):
    """Raised when MiroFish cannot be reached or fails its health check."""


class MiroFishHealthClient:
    """Read-only client for checking MiroFish service availability."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        parsed = urlsplit(base_url)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be a valid HTTP(S) URL")

        if parsed.username or parsed.password:
            raise ValueError("Do not include credentials in base_url")

        if parsed.query or parsed.fragment:
            raise ValueError("base_url must not contain a query or fragment")

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def check_health(self) -> dict[str, Any]:
        """Check service health without creating or modifying any resources."""
        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.get(f"{self.base_url}/health")
                response.raise_for_status()

                payload = response.json()

        except (httpx.HTTPError, ValueError) as exc:
            raise MiroFishConnectionError(
                "MiroFish health check failed. Verify the URL, "
                "service availability, HTTP status, and JSON response."
            ) from exc

        if not isinstance(payload, dict):
            raise MiroFishConnectionError(
                "MiroFish health response must be a JSON object."
            )

        if (
            payload.get("status") != "ok"
            or payload.get("service") != "MiroFish Backend"
        ):
            raise MiroFishConnectionError(
                "The endpoint did not identify itself as a healthy "
                "MiroFish Backend."
            )

        return {
            "status": "ok",
            "service": "MiroFish Backend",
            "endpoint": "/health",
        }
