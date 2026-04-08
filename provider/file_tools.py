from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


def normalize_api_base_url(raw_url: str) -> str:
    trimmed = (raw_url or "").strip()
    if not trimmed:
        raise ToolProviderCredentialValidationError("Either api_base_url or api_uri is required")

    parsed = urlparse(trimmed if "://" in trimmed else f"https://{trimmed}")
    if not parsed.scheme or not parsed.netloc or " " in parsed.netloc:
        raise ToolProviderCredentialValidationError(
            "API base URL must include a valid host, for example https://api.dify.ai/v1"
        )

    if parsed.scheme not in {"http", "https"}:
        raise ToolProviderCredentialValidationError("API base URL scheme must be http or https")

    normalized = trimmed if "://" in trimmed else f"https://{trimmed}"
    return normalized.rstrip("/")


class FileToolsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        raw_url = credentials.get("api_base_url") or credentials.get("api_uri") or ""
        normalize_api_base_url(raw_url)

        api_key = (credentials.get("api_key") or "").strip()
        if not api_key:
            raise ToolProviderCredentialValidationError("api_key is required")
