from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.routes.base import BaseRoute
from litestar.types import WebSocketScope

if TYPE_CHECKING:
    from litestar.handlers.websocket_handlers import WebsocketRouteHandler
    from litestar.types import Receive, Send


class WebSocketRoute(BaseRoute[WebSocketScope]):
    """A websocket route, handling a single ``WebsocketRouteHandler``"""

    __slots__ = ("route_handler",)

    def __init__(
        self,
        *,
        path: str,
        route_handler: WebsocketRouteHandler,
    ) -> None:
        """Initialize the route.

        Args:
            path: The path for the route.
            route_handler: An instance of :class:`~.handlers.WebsocketRouteHandler`.
        """
        self.route_handler = route_handler

        super().__init__(path=path)

    async def handle(self, scope: WebSocketScope, receive: Receive, send: Send) -> None:
        """ASGI app that creates a WebSocket from the passed in args, and then awaits the handler function.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None
        """
        socket = self.route_handler.websocket_class(scope=scope, receive=receive, send=send)
        await self.route_handler.handle(connection=socket)
