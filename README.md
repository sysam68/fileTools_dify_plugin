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
- **Upload from Content**
  - Convert input text or base64 encoded binary data into a native Dify file output
- **Upload from URL**
  - Download a file from a public or signed URL and return it as a native Dify file output

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

### ✅ Upload from Content

This tool converts input text or base64 encoded binary data into a native Dify `blob` file output. Dify creates the actual file object and URLs downstream, instead of the plugin reconstructing them manually.

You can specify the file name, MIME type, and the format of the content:

- To save plain text as a file:
  - `content`: `Hello, world!`
  - `filename`: `hello.txt`
  - `format`: `text`

- To save base64 encoded data as a file:
  - `content`: `SGVsbG8sIHdvcmxkIQ==`
  - `filename`: `hello.txt`
  - `format`: `base64`

This tool is useful for turning generated content or decoded binary data into a reusable file output.

If you leave the MIME type empty, it will be automatically determined based on the file name. Of course, you can also specify a MIME type explicitly using the `mime_type` option.

When the `format` is set to `text`, you can also specify the encoding using the `encoding` option (e.g., `utf-8`, `shift_jis`, `euc-jp`). If not specified, it defaults to `utf-8`.

No provider credentials are required for this flow.

### ✅ Upload from URL

This tool downloads a file from a public or signed URL and returns it as a native Dify `blob` file output.

Typical inputs:

- `input_file`: a standard Dify file object containing `url` or `remote_url`
- `url`: a reachable file URL, including signed Dify file preview URLs such as `https://example.dify.ai/files/<file_id>/file-preview?...`
- `filename`: optional explicit override if the source response does not expose a useful file name
- `mime_type`: optional explicit override if the source response does not expose a useful content type

If both are present, `url` overrides `input_file.url`.

When `filename` is empty, the tool tries, in order:

- `input_file.filename`
- `Content-Disposition`
- the URL path when it contains a real file name
- a generated fallback name based on the detected MIME type

## Related Links

- **Icon**: [Heroicons](https://heroicons.com/)
