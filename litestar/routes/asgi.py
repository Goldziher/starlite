from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from litestar.connection import ASGIConnection
from litestar.exceptions import LitestarWarning
from litestar.routes.base import BaseRoute
from litestar.types import Scope

if TYPE_CHECKING:
    from litestar.handlers.asgi_handlers import ASGIRouteHandler
    from litestar.types import Receive, Send


class ASGIRoute(BaseRoute[Scope]):
    """An ASGI route, handling a single ``ASGIRouteHandler``"""

    __slots__ = ("route_handler",)

    def __init__(
        self,
        *,
        path: str,
        route_handler: ASGIRouteHandler,
    ) -> None:
        """Initialize the route.

        Args:
            path: The path for the route.
            route_handler: An instance of :class:`~.handlers.ASGIRouteHandler`.
        """
        self.route_handler = route_handler
        super().__init__(path=path)

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI app that authorizes the connection and then awaits the handler function.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None
        """

        handler_scope = scope.copy()
        copy_scope = self.route_handler.copy_scope

        connection = ASGIConnection["ASGIRouteHandler", Any, Any, Any](
            scope=handler_scope if copy_scope is True else scope,
            receive=receive,
            send=send,
        )
        await self.route_handler.handle(connection=connection)

        if copy_scope is None and handler_scope != scope:
            warnings.warn(
                f"{self.route_handler}: Mounted ASGI app {self.route_handler.fn} modified 'scope' with 'copy_scope' "
                "set to 'None'. Set 'copy_scope=True' to avoid mutating the original scope or set 'copy_scope=False' "
                "if mutating the scope from within the mounted ASGI app is intentional. Note: 'copy_scope' will "
                "default to 'True' by default in Litestar 3",
                category=LitestarWarning,
                stacklevel=1,
            )
