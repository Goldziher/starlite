from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.exceptions import ImproperlyConfiguredException
from litestar.routes.base import BaseRoute
from litestar.types import HTTPScope

if TYPE_CHECKING:
    from collections.abc import Iterable

    from litestar.handlers.http_handlers import HTTPRouteHandler
    from litestar.types import Receive, Send
    from litestar.types.asgi_types import HttpMethodName


class HTTPRoute(BaseRoute[HTTPScope]):
    """An HTTP route, capable of handling multiple ``HTTPRouteHandler``\\ s."""  # noqa: D301

    __slots__ = (
        "route_handler_map",
        "route_handlers",
    )

    def __init__(
        self,
        *,
        path: str,
        route_handlers: Iterable[HTTPRouteHandler],
    ) -> None:
        """Initialize ``HTTPRoute``.

        Args:
            path: The path for the route.
            route_handlers: A list of :class:`~.handlers.HTTPRouteHandler`.
        """
        super().__init__(path=path)
        self.route_handler_map: dict[HttpMethodName, HTTPRouteHandler] = self.create_handler_map(route_handlers)
        self.route_handlers = tuple(self.route_handler_map.values())
        self.methods = tuple(self.route_handler_map)

    async def handle(self, scope: HTTPScope, receive: Receive, send: Send) -> None:
        """ASGI app that creates a Request from the passed in args, determines which handler function to call and then
        handles the call.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None
        """
        route_handler = self.route_handler_map[scope["method"]]
        connection = route_handler.request_class(scope=scope, receive=receive, send=send)
        await route_handler.handle(connection=connection)

    def create_handler_map(self, route_handlers: Iterable[HTTPRouteHandler]) -> dict[HttpMethodName, HTTPRouteHandler]:
        """Parse the ``router_handlers`` of this route and return a mapping of
        http- methods and route handlers.
        """
        handler_map = {}
        for route_handler in route_handlers:
            for http_method in route_handler.http_methods:
                if http_method in handler_map:
                    raise ImproperlyConfiguredException(
                        f"Handler already registered for path {self.path!r} and http method {http_method}"
                    )
                handler_map[http_method] = route_handler
        return handler_map
