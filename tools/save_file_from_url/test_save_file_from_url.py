from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from dify_plugin.entities.tool import ToolRuntime


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.save_file_from_url.save_file_from_url import SaveFileFromUrlTool  # noqa: E402


def test_save_file_from_url_returns_only_files_variable() -> None:
    runtime = ToolRuntime(
        credentials={"api_base_url": "https://api.example.com", "api_key": "secret"},
        user_id=None,
        session_id=None,
    )
    tool = SaveFileFromUrlTool(runtime=runtime, session=MagicMock())

    saved_file = {
        "dify_model_identity": "__dify__file__",
        "id": None,
        "tenant_id": "tenant-1",
        "type": "image",
        "transfer_method": "local_file",
        "remote_url": "https://example.com/file-preview",
        "related_id": "file-123",
        "filename": "capture.png",
        "extension": ".png",
        "mime_type": "image/png",
        "size": 42,
        "url": "https://example.com/file-preview",
    }

    with (
        patch("tools.save_file_from_url.save_file_from_url.resolve_source_url", return_value="https://example.com/source"),
        patch(
            "tools.save_file_from_url.save_file_from_url.download_remote_file",
            return_value=("capture.png", "image/png", b"png-bytes"),
        ),
        patch(
            "tools.save_file_from_url.save_file_from_url.upload_file",
            return_value={"id": "file-123"},
        ),
        patch("tools.save_file_from_url.save_file_from_url.to_dify_file", return_value=saved_file),
    ):
        messages = list(
            tool._invoke(
                {
                    "input_file": {"filename": "capture.png", "mime_type": "image/png"},
                    "url": "",
                    "user": "",
                    "filename": "",
                    "mime_type": "",
                }
            )
        )

    assert len(messages) == 1
    assert messages[0].message.variable_name == "files"
    assert messages[0].message.variable_value == [saved_file]
