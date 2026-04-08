from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from provider.file_tools import normalize_api_base_url

from ._upload_helpers import (
    build_file_blob,
    optional_string_parameter,
    require_string_parameter,
    resolve_mime_type,
    to_dify_file,
    upload_file,
)


class SaveAsFileTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        content = tool_parameters.get("content")
        filename = require_string_parameter(tool_parameters, "filename")
        user = optional_string_parameter(tool_parameters, "user")
        mime_type = tool_parameters.get("mime_type", "")
        format = tool_parameters.get("format", "text")
        encoding = tool_parameters.get("encoding", "") or "utf-8"

        api_base_url = normalize_api_base_url(
            self.runtime.credentials.get("api_base_url") or self.runtime.credentials.get("api_uri") or ""
        )
        api_key = require_string_parameter(self.runtime.credentials, "api_key")

        resolved_mime_type = resolve_mime_type(filename, mime_type)
        file_blob = build_file_blob(content, format, encoding)
        upload_result = upload_file(
            api_base_url=api_base_url,
            api_key=api_key,
            user=user,
            filename=filename,
            mime_type=resolved_mime_type,
            file_blob=file_blob,
        )

        yield self.create_json_message(to_dify_file(upload_result))
