from __future__ import annotations

import base64
import binascii
import codecs
import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, unquote

import httpx

DEFAULT_TIMEOUT_SECONDS = 30.0


def resolve_download_url(raw_url: str) -> str:
    trimmed = (raw_url or "").strip()
    if not trimmed:
        raise ValueError("url is required")

    parsed = urlparse(trimmed)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be a valid http or https URL")

    return trimmed


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


def optional_string_parameter(tool_parameters: dict[str, Any], name: str) -> str | None:
    value = tool_parameters.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string when provided")

    trimmed = value.strip()
    return trimmed or None


def resolve_filename(filename: str | None, download_url: str, headers: httpx.Headers, mime_type: str) -> str:
    candidate = (filename or "").strip()
    if candidate:
        return candidate

    from_header = _filename_from_content_disposition(headers.get("content-disposition"))
    if from_header:
        return from_header

    parsed = urlparse(download_url)
    path_name = Path(unquote(parsed.path)).name.strip()
    if path_name and path_name not in {"file-preview", "image-preview"} and "." in path_name:
        return path_name

    extension = mimetypes.guess_extension(mime_type, strict=False) or ""
    return f"downloaded-file{extension}"


def download_remote_file(
    *,
    url: str,
    filename: str | None = None,
    mime_type: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[str, str, bytes]:
    resolved_url = resolve_download_url(url)

    try:
        with httpx.Client(timeout=httpx.Timeout(timeout_seconds), follow_redirects=True) as client:
            response = client.get(resolved_url, headers={"Accept": "*/*"})
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to download source file: {exc!s}") from exc

    if response.status_code != 200:
        raise RuntimeError(build_download_http_error_message(response))

    file_blob = response.content
    if not file_blob:
        raise RuntimeError("Source URL returned an empty response body")

    resolved_mime_type = resolve_download_mime_type(filename, mime_type, response.headers)
    resolved_filename = resolve_filename(filename, resolved_url, response.headers, resolved_mime_type)
    return resolved_filename, resolved_mime_type, file_blob


def build_upload_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/files/upload"


def upload_file(
    *,
    api_base_url: str,
    api_key: str,
    user: str | None,
    filename: str,
    mime_type: str,
    file_blob: bytes,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    files = {"file": (filename, file_blob, mime_type)}
    data = {"user": user} if user is not None else None

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


def build_download_http_error_message(response: httpx.Response) -> str:
    hint = {
        400: "Source URL request was rejected.",
        401: "Source URL requires authentication.",
        403: "Source URL access is forbidden.",
        404: "Source file was not found.",
        408: "Source URL request timed out.",
        415: "Source server returned an unsupported media type.",
        429: "Source URL is rate limited.",
        500: "Source server returned an internal server error.",
        502: "Source server returned a bad gateway response.",
        503: "Source server is temporarily unavailable.",
        504: "Source server timed out.",
    }.get(response.status_code)

    detail = response.text.strip() or None
    message_parts = [f"Source file download failed with HTTP {response.status_code}"]
    if hint:
        message_parts.append(hint)
    if detail:
        message_parts.append(detail)
    return " - ".join(message_parts)


def resolve_download_mime_type(filename: str | None, mime_type: str | None, headers: httpx.Headers) -> str:
    explicit_mime_type = (mime_type or "").strip()
    if explicit_mime_type:
        return explicit_mime_type

    header_mime_type = (headers.get("content-type") or "").split(";", 1)[0].strip()
    if header_mime_type:
        return header_mime_type

    fallback_filename = (filename or "").strip()
    if fallback_filename:
        guessed, _ = mimetypes.guess_type(fallback_filename)
        if guessed:
            return guessed

    raise ValueError(
        "MIME type could not be determined from the source URL response. Please provide mime_type explicitly."
    )


def _filename_from_content_disposition(raw_header: str | None) -> str | None:
    if not raw_header:
        return None

    for part in raw_header.split(";"):
        key, separator, value = part.strip().partition("=")
        if separator != "=":
            continue

        normalized_key = key.strip().lower()
        normalized_value = value.strip().strip('"')
        if normalized_key == "filename*" and normalized_value.lower().startswith("utf-8''"):
            decoded = unquote(normalized_value[7:])
            if decoded:
                return Path(decoded).name
        if normalized_key == "filename" and normalized_value:
            return Path(normalized_value).name

    return None
