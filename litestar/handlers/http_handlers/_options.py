from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.enums import HttpMethod, MediaType
from litestar.handlers import HTTPRouteHandler
from litestar.response import Response
from litestar.status_codes import HTTP_204_NO_CONTENT

if TYPE_CHECKING:
    from collections.abc import Iterable

    from litestar.types import Method


def create_options_handler(path: str, allow_methods: Iterable[Method]) -> HTTPRouteHandler:
    """Args:
        path: The route path

    Returns:
        An HTTP route handler for OPTIONS requests.
    """

    def options_handler() -> Response:
        """Handler function for OPTIONS requests.

        Returns:
            Response
        """
        return Response(
            content=None,
            status_code=HTTP_204_NO_CONTENT,
            headers={"Allow": ", ".join(sorted(allow_methods))},  # pyright: ignore
            media_type=MediaType.TEXT,
        )

    return HTTPRouteHandler(
        path=path, http_method=[HttpMethod.OPTIONS], include_in_schema=False, sync_to_thread=False, fn=options_handler
    )
