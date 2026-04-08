from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from provider.file_tools import normalize_api_base_url

from tools.save_as_file._upload_helpers import (
    download_remote_file,
    optional_string_parameter,
    read_file_attribute,
    require_string_parameter,
    resolve_source_url,
    to_dify_file,
    upload_file,
)


class SaveFileFromUrlTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        input_file = tool_parameters.get("input_file")
        url = resolve_source_url(tool_parameters, input_file)
        user = optional_string_parameter(tool_parameters, "user")
        filename = optional_string_parameter(tool_parameters, "filename") or read_file_attribute(input_file, "filename", "name")
        mime_type = optional_string_parameter(tool_parameters, "mime_type") or read_file_attribute(input_file, "mime_type")

        api_base_url = normalize_api_base_url(
            self.runtime.credentials.get("api_base_url") or self.runtime.credentials.get("api_uri") or ""
        )
        api_key = require_string_parameter(self.runtime.credentials, "api_key")

        resolved_filename, resolved_mime_type, file_blob = download_remote_file(
            url=url,
            filename=filename,
            mime_type=mime_type,
        )
        upload_result = upload_file(
            api_base_url=api_base_url,
            api_key=api_key,
            user=user,
            filename=resolved_filename,
            mime_type=resolved_mime_type,
            file_blob=file_blob,
        )

        yield self.create_json_message(to_dify_file(upload_result))
