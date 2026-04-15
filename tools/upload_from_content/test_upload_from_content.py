from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

from dify_plugin.entities.tool import ToolRuntime


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.upload_from_content.upload_from_content import UploadFromContentTool  # noqa: E402


def test_upload_from_content_returns_blob_message() -> None:
    runtime = ToolRuntime(credentials={}, user_id=None, session_id=None)
    tool = UploadFromContentTool(runtime=runtime, session=MagicMock())

    messages = list(
        tool._invoke(
            {
                "content": "Hello",
                "filename": "hello.txt",
                "mime_type": "",
                "format": "text",
                "encoding": "utf-8",
            }
        )
    )

    assert len(messages) == 1
    assert messages[0].message.blob == b"Hello"
    assert messages[0].meta == {"filename": "hello.txt", "mime_type": "text/plain"}
