from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import get
from litestar.enums import MediaType
from litestar.openapi.plugins import OpenAPIRenderPlugin

if TYPE_CHECKING:
    from litestar.connection import Request
    from litestar.router import Router


class MyOpenAPIPlugin(OpenAPIRenderPlugin):
    def render(self, request: Request, openapi_schema: dict[str, str]) -> bytes:
        return b"<html>My UI of Choice!</html>"

    def receive_router(self, router: Router) -> None:
        @get("/something", media_type=MediaType.TEXT)
        def something() -> str:
            return "Something"

        router.register(something)
