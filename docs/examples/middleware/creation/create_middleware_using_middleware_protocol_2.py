import logging

from litestar import Request
from litestar.middleware.base import MiddlewareProtocol
from litestar.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class MyRequestLoggingMiddleware(MiddlewareProtocol):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            request = Request(scope)
            logger.info("%s - %s" % request.method, request.url)
        await self.app(scope, receive, send)
