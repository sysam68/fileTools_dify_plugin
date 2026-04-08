from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.save_as_file._upload_helpers import (  # noqa: E402
    build_file_blob,
    build_download_http_error_message,
    build_http_error_message,
    download_remote_file,
    optional_string_parameter,
    resolve_mime_type,
    upload_file,
)


def test_build_file_blob_text_utf8() -> None:
    assert build_file_blob("Hello", "text", "utf-8") == b"Hello"


def test_build_file_blob_invalid_encoding() -> None:
    with pytest.raises(ValueError, match="Invalid encoding"):
        build_file_blob("Hello", "text", "invalid-encoding")


def test_build_file_blob_invalid_base64() -> None:
    with pytest.raises(ValueError, match="not valid base64"):
        build_file_blob("%%%not-base64%%%", "base64", "utf-8")


def test_resolve_mime_type_from_filename() -> None:
    assert resolve_mime_type("image.png", "") == "image/png"


def test_resolve_mime_type_requires_explicit_value_when_unknown() -> None:
    with pytest.raises(ValueError, match="MIME type could not be determined"):
        resolve_mime_type("file.unknown-extension", "")


def test_upload_file_returns_json_payload_unchanged() -> None:
    payload = {"id": "123", "name": "demo.txt"}
    response = MagicMock()
    response.status_code = 201
    response.json.return_value = payload

    client = MagicMock()
    client.post.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    with patch("tools.save_as_file._upload_helpers.httpx.Client", return_value=client) as client_cls:
        result = upload_file(
            api_base_url="https://api.dify.ai/v1",
            api_key="secret",
            user="workflow-user",
            filename="demo.txt",
            mime_type="text/plain",
            file_blob=b"hello",
        )

    assert result == payload
    _, kwargs = client.post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer secret"
    assert kwargs["data"] == {"user": "workflow-user"}
    assert kwargs["files"]["file"] == ("demo.txt", b"hello", "text/plain")
    client_cls.assert_called_once()


def test_upload_file_omits_user_field_when_not_provided() -> None:
    payload = {"id": "123", "name": "demo.txt"}
    response = MagicMock()
    response.status_code = 201
    response.json.return_value = payload

    client = MagicMock()
    client.post.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    with patch("tools.save_as_file._upload_helpers.httpx.Client", return_value=client):
        result = upload_file(
            api_base_url="https://api.dify.ai/v1",
            api_key="secret",
            user=None,
            filename="demo.txt",
            mime_type="text/plain",
            file_blob=b"hello",
        )

    assert result == payload
    _, kwargs = client.post.call_args
    assert kwargs["data"] is None


def test_upload_file_raises_useful_http_error() -> None:
    response = httpx.Response(
        401,
        json={"message": "Invalid API key"},
        request=httpx.Request("POST", "https://api.dify.ai/v1/files/upload"),
    )

    with pytest.raises(RuntimeError, match="HTTP 401"):
        raise RuntimeError(build_http_error_message(response))


def test_upload_file_rejects_non_json_success_response() -> None:
    response = MagicMock()
    response.status_code = 201
    response.json.side_effect = json.JSONDecodeError("bad json", "x", 0)

    client = MagicMock()
    client.post.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    with patch("tools.save_as_file._upload_helpers.httpx.Client", return_value=client):
        with pytest.raises(RuntimeError, match="non-JSON response"):
            upload_file(
                api_base_url="https://api.dify.ai/v1",
                api_key="secret",
                user="workflow-user",
                filename="demo.txt",
                mime_type="text/plain",
                file_blob=b"hello",
            )


def test_download_remote_file_uses_content_disposition_filename() -> None:
    response = httpx.Response(
        200,
        headers={
            "Content-Type": "image/png",
            "Content-Disposition": 'attachment; filename="capture.png"',
        },
        content=b"png-bytes",
        request=httpx.Request("GET", "https://example.com/file-preview"),
    )

    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    with patch("tools.save_as_file._upload_helpers.httpx.Client", return_value=client):
        filename, mime_type, file_blob = download_remote_file(url="https://example.com/file-preview")

    assert filename == "capture.png"
    assert mime_type == "image/png"
    assert file_blob == b"png-bytes"


def test_download_remote_file_generates_filename_from_mime_type() -> None:
    response = httpx.Response(
        200,
        headers={"Content-Type": "image/png"},
        content=b"png-bytes",
        request=httpx.Request("GET", "https://example.com/files/123/file-preview"),
    )

    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    with patch("tools.save_as_file._upload_helpers.httpx.Client", return_value=client):
        filename, mime_type, file_blob = download_remote_file(url="https://example.com/files/123/file-preview")

    assert filename == "downloaded-file.png"
    assert mime_type == "image/png"
    assert file_blob == b"png-bytes"


def test_download_remote_file_raises_useful_http_error() -> None:
    response = httpx.Response(
        404,
        text="Not Found",
        request=httpx.Request("GET", "https://example.com/files/missing"),
    )

    with pytest.raises(RuntimeError, match="HTTP 404"):
        raise RuntimeError(build_download_http_error_message(response))


def test_optional_string_parameter_accepts_empty_value() -> None:
    assert optional_string_parameter({"user": ""}, "user") is None
