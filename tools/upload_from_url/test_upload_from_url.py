from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from dify_plugin.entities.tool import ToolRuntime


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.upload_from_url.upload_from_url import UploadFromUrlTool  # noqa: E402


def test_upload_from_url_returns_blob_message() -> None:
    runtime = ToolRuntime(
        credentials={"api_base_url": "https://api.example.com", "api_key": "secret"},
        user_id=None,
        session_id=None,
    )
    tool = UploadFromUrlTool(runtime=runtime, session=MagicMock())

    with (
        patch("tools.upload_from_url.upload_from_url.resolve_source_url", return_value="https://example.com/source"),
        patch(
            "tools.upload_from_url.upload_from_url.download_remote_file",
            return_value=("capture.png", "image/png", b"png-bytes"),
        ),
    ):
        messages = list(
            tool._invoke(
                {
                    "input_file": {"filename": "capture.png", "mime_type": "image/png"},
                    "url": "",
                    "filename": "",
                    "mime_type": "",
                }
            )
        )

    assert len(messages) == 1
    assert messages[0].message.blob == b"png-bytes"
    assert messages[0].meta == {"filename": "capture.png", "mime_type": "image/png"}
