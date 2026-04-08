from __future__ import annotations

import base64
import binascii
import codecs
import json
import mimetypes
from typing import Any

import httpx

DEFAULT_TIMEOUT_SECONDS = 30.0


def resolve_mime_type(filename: str, mime_type: str | None) -> str:
    resolved = (mime_type or "").strip()
    if resolved:
        return resolved

    guessed, _ = mimetypes.guess_type(filename)
    if guessed:
        return guessed

    raise ValueError(
        "MIME type could not be determined by filename. Please provide a valid MIME type explicitly."
    )


def build_file_blob(content: Any, content_format: str, encoding: str) -> bytes:
    if not isinstance(content, str) or not content:
        raise ValueError("content is required")

    normalized_format = (content_format or "text").strip().lower()
    if normalized_format not in {"text", "base64"}:
        raise ValueError("format must be either 'text' or 'base64'")

    if normalized_format == "text":
        try:
            codecs.lookup(encoding)
        except LookupError as exc:
            raise ValueError(f"Invalid encoding: '{encoding}'. Please provide a valid Python encoding name.") from exc
        try:
            return content.encode(encoding)
        except UnicodeEncodeError as exc:
            raise ValueError(f"Content cannot be encoded with '{encoding}': {exc}") from exc

    try:
        return base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("content is not valid base64 data") from exc


def require_string_parameter(tool_parameters: dict[str, Any], name: str) -> str:
    value = tool_parameters.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def build_upload_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/files/upload"


def upload_file(
    *,
    api_base_url: str,
    api_key: str,
    user: str,
    filename: str,
    mime_type: str,
    file_blob: bytes,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    files = {"file": (filename, file_blob, mime_type)}
    data = {"user": user}

    try:
        with httpx.Client(timeout=httpx.Timeout(timeout_seconds), follow_redirects=True) as client:
            response = client.post(build_upload_url(api_base_url), headers=headers, data=data, files=files)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to call Dify Files API: {exc!s}") from exc

    if response.status_code != 201:
        raise RuntimeError(build_http_error_message(response))

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("Dify Files API returned a non-JSON response for upload") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Dify Files API returned an unexpected upload payload")

    return payload


def build_http_error_message(response: httpx.Response) -> str:
    hint = {
        400: "Request rejected. Verify file content, filename, MIME type, and user.",
        401: "Authentication failed. Verify that api_key is valid.",
        403: "Access denied. Ensure the API key can upload files for this application.",
        413: "Uploaded file is too large for the current Dify configuration.",
        415: "Unsupported media type. Verify the MIME type and file content.",
        429: "Rate limited. Retry after a short delay.",
        500: "Dify reported an internal server error.",
        502: "Dify upstream returned a bad gateway response.",
        503: "Dify service is temporarily unavailable.",
        504: "Dify service timed out while processing the upload.",
    }.get(response.status_code)

    detail = None
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail = payload.get("message") or payload.get("error") or payload.get("detail")
    except json.JSONDecodeError:
        detail = response.text.strip() or None

    message_parts = [f"Dify Files API upload failed with HTTP {response.status_code}"]
    if hint:
        message_parts.append(hint)
    if detail:
        message_parts.append(str(detail))
    return " - ".join(message_parts)
