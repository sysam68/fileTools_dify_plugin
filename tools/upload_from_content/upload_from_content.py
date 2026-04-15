from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from ._upload_helpers import (
    build_file_blob,
    require_string_parameter,
    resolve_mime_type,
)


class UploadFromContentTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        content = tool_parameters.get("content")
        filename = require_string_parameter(tool_parameters, "filename")
        mime_type = tool_parameters.get("mime_type", "")
        format = tool_parameters.get("format", "text")
        encoding = tool_parameters.get("encoding", "") or "utf-8"

        resolved_mime_type = resolve_mime_type(filename, mime_type)
        file_blob = build_file_blob(content, format, encoding)
        yield self.create_blob_message(
            blob=file_blob,
            meta={
                "filename": filename,
                "mime_type": resolved_mime_type,
            },
        )
