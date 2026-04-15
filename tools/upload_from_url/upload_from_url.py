from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.upload_from_content._upload_helpers import (
    download_remote_file,
    optional_string_parameter,
    read_file_attribute,
    resolve_source_url,
)


class UploadFromUrlTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        input_file = tool_parameters.get("input_file")
        url = resolve_source_url(tool_parameters, input_file)
        filename = optional_string_parameter(tool_parameters, "filename") or read_file_attribute(input_file, "filename", "name")
        mime_type = optional_string_parameter(tool_parameters, "mime_type") or read_file_attribute(input_file, "mime_type")

        resolved_filename, resolved_mime_type, file_blob = download_remote_file(
            url=url,
            filename=filename,
            mime_type=mime_type,
        )
        yield self.create_blob_message(
            blob=file_blob,
            meta={
                "filename": resolved_filename,
                "mime_type": resolved_mime_type,
            },
        )
