from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from provider.file_tools import normalize_api_base_url

from tools.save_as_file._upload_helpers import (
    download_remote_file,
    optional_string_parameter,
    require_string_parameter,
    upload_file,
)


class SaveFileFromUrlTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        url = require_string_parameter(tool_parameters, "url")
        user = optional_string_parameter(tool_parameters, "user")
        filename = tool_parameters.get("filename")
        mime_type = tool_parameters.get("mime_type")

        api_base_url = normalize_api_base_url(
            self.runtime.credentials.get("api_base_url") or self.runtime.credentials.get("api_uri") or ""
        )
        api_key = require_string_parameter(self.runtime.credentials, "api_key")

        resolved_filename, resolved_mime_type, file_blob = download_remote_file(
            url=url,
            filename=filename,
            mime_type=mime_type,
        )
        result = upload_file(
            api_base_url=api_base_url,
            api_key=api_key,
            user=user,
            filename=resolved_filename,
            mime_type=resolved_mime_type,
            file_blob=file_blob,
        )

        yield self.create_json_message(result)
