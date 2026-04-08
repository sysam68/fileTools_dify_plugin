# 📦 File Tools - A collection of various tools for handling file object

- **Plugin ID** : sysam68/file_tools
- **Author** : sysam68
- **Type** : tool
- **Repository** : https://github.com/sysam68/fileTools_dify_plugin

## ✨ Overview

A collection of various tools for handling file objects:

- **Dump to JSON**
  - Dump a file object as a JSON string for debugging
- **Embed as Base64**
  - Convert a file to data URI format (Base64 encoded), optionally in markdown format
- **Get Download URL**
  - Get a download URL for a file object, optionally as a markdown link
- **Save as File**
  - Save input text or base64 encoded binary data as a file with specified file name and MIME type
- **Save File from URL**
  - Download a file from a public or signed URL, then upload it to Dify Files

## 🛠️ Bundled Tools

### ✅ Dump to JSON

This is a tool to dump a file object as a JSON string for debugging purposes. This is an example of the output:

```json
{
  "dify_model_identity": "__dify__file__",
  "url": "https://upload.dify.ai/files/tools/62edee2e-ac72-43fc-aa6a-c8b82ba2f0d3.md?timestamp=...&nonce=...&sign=...",
  "mime_type": "text/markdown",
  "filename": "sample.md",
  "extension": ".md",
  "size": 861,
  "type": "document",
  "blob": "IyBBIHNhbXBsZSBv...RWxGVGtTdVFtQ0Mp"
}
```

This tool is useful for inspecting a file object.

You can choose whether to include the base64 encoded binary data in the `blob` field, by `include_blob` option.

### ✅ Embed as Base64

This is a tool to convert a file to data URI format (Base64 encoded) such as:

```markdown
# Converted PNG image, in "plain" format
data:image/png;base64,iVBORw0KGgoAAAAN...AAAAAElFTkSuQmCC

# Converted PNG image, in "markdown" format
![Awesome Image](data:image/png;base64,iVBORw0KGgoAAAAN...AAAAAElFTkSuQmCC)

# Converted text file, in "plain" format
data:text/plain;base64,SGVsbG8sIHdvcmxkIQ==

# Converted text file, in "markdown" format
[Click to View Text](data:text/plain;base64,SGVsbG8sIHdvcmxkIQ==)
```

This tool is useful for embedding files or images directly into markdown documents, HTML pages, or any other formats that support data URIs.

If you select the `plain` format (default), the output will be a plain data URI string.
If you select the `markdown` format, the output will be an image (`![text](...)`) or a link (`[text](...)`) depending on whether the file is an image or not.  
You can customize the link text (or alt text for images) by using the `link_text` option. If the `link_text` is not provided, it will default to the file name.

The MIME type will be automatically determined based on the file name, but you can also pass a MIME type explicitly using the `mime_type` option.

### ✅ Get Download URL

This is a tool to generate a download link for a file object, either as a plain URL or in markdown format:

```markdown
# In "plain" format
https://upload.dify.ai/files/tools/62edee2e-ac72-43fc-aa6a-c8b82ba2f0d3.md?timestamp=...&nonce=...&sign=...

# In "markdown" format
[Click to Download](https://upload.dify.ai/files/tools/62edee2e-ac72-43fc-aa6a-c8b82ba2f0d3.md?timestamp=...&nonce=...&sign=...)
```

This tool is useful when you want to pass a file download link to another node, or when you want to embed a file download link as part of a nicely formatted chatbot response.

If you select the `plain` format (default), the output will be a plain URL string.
If you select the `markdown` format, the output will be a link (`[text](...)`) with the file name or a custom text (by `link_text`).

### ✅ Save as File

This tool now uploads input text or base64 encoded binary data through Dify's public Files API (`POST /files/upload`) and returns the raw file object JSON produced by Dify. You can specify the file name, MIME type, file content format, and the `user` identifier required by the API.

The returned JSON follows Dify's upload response shape, for example:

```json
{
  "id": "f4a5066e-68a0-421a-b0fd-482af8361bf1",
  "name": "Capture d'écran 23.03.2026 à 10.23.29 AM.png",
  "size": 505510,
  "extension": "png",
  "mime_type": "image/png",
  "created_by": "c48a50b8-efec-49a2-b513-8c06ec4c1927",
  "created_at": 1775646988,
  "preview_url": null,
  "source_url": "https://example.dify.ai/files/f4a5066e-68a0-421a-b0fd-482af8361bf1/file-preview?...",
  "original_url": null,
  "user_id": null,
  "tenant_id": "50325c9b-1282-4765-8541-5607ffcbbab2",
  "conversation_id": null,
  "file_key": null
}
```

You can specify the file name, MIME type, and the format of the content:

- To save plain text as a file:
  - `content`: `Hello, world!`
  - `filename`: `hello.txt`
  - `format`: `text`

- To save base64 encoded data as a file:
  - `content`: `SGVsbG8sIHdvcmxkIQ==`
  - `filename`: `hello.txt`
  - `format`: `base64`

This tool is useful for saving generated content or decoded binary data as a downloadable file.

If you leave the MIME type empty, it will be automatically determined based on the file name. Of course, you can also specify a MIME type explicitly using the `mime_type` option.

When the `format` is set to `text`, you can also specify the encoding using the `encoding` option (e.g., `utf-8`, `shift_jis`, `euc-jp`). If not specified, it defaults to `utf-8`.

Provider configuration is now required:

- `api_base_url` or `api_uri`: Dify public API base URL, for example `https://api.dify.ai/v1`
- `api_key`: Dify API key used for file uploads

This release only implements the upload endpoint. The preview/download endpoint remains available downstream in Dify as `GET /files/{file_id}/preview`.

### ✅ Save File from URL

This tool downloads a file from a public or signed URL, then uploads the downloaded binary to Dify's public Files API (`POST /files/upload`) and returns the raw file object JSON produced by Dify.

Typical inputs:

- `url`: a reachable file URL, including signed Dify file preview URLs such as `https://example.dify.ai/files/<file_id>/file-preview?...`
- `user`: the Dify user identifier required by the Files API
- `filename`: optional explicit override if the source response does not expose a useful file name
- `mime_type`: optional explicit override if the source response does not expose a useful content type

When `filename` is empty, the tool tries, in order:

- `Content-Disposition`
- the URL path when it contains a real file name
- a generated fallback name based on the detected MIME type

## Related Links

- **Icon**: [Heroicons](https://heroicons.com/)
