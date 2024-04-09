from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from litestar.connection import Request
from litestar.openapi.plugins import OpenAPIRenderPlugin


class ScalarRenderPlugin(OpenAPIRenderPlugin):
    def __init__(
        self,
        *,
        version: str = "1.19.5",
        js_url: str | None = None,
        css_url: str | None = None,
        path: str | Sequence[str] = "/scalar",
        **kwargs: Any,
    ) -> None:
        self.js_url = js_url or f"https://cdn.jsdelivr.net/npm/@scalar/api-reference@{version}"
        self.css_url = css_url
        super().__init__(path=path, **kwargs)

    def render(self, request: Request, openapi_schema: dict[str, Any]) -> bytes:
        style_sheet_link = f'<link rel="stylesheet" type="text/css" href="{self.css_url}">' if self.css_url else ""
        head = f"""
                  <head>
                    <title>{openapi_schema["info"]["title"]}</title>
                    {self.style}
                    <meta charset="utf-8"/>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    {self.favicon}
                    {style_sheet_link}
                  </head>
                """

        body = f"""
                <script
                  id="api-reference"
                  data-url="openapi.json">
                </script>
                <script src="{self.js_url}" crossorigin></script>
                """

        return f"""
                <!DOCTYPE html>
                    <html>
                        {head}
                        {body}
                    </html>
                """.encode()
