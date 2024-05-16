from litestar import Request
from litestar.middleware.base import MiddlewareProtocol
from litestar.response.redirect import ASGIRedirectResponse
from litestar.types import ASGIApp, Receive, Scope, Send


class RedirectMiddleware(MiddlewareProtocol):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if Request(scope).session is None:
            response = ASGIRedirectResponse(path="/login")
            await response(scope, receive, send)
        else:
            await self.app(scope, receive, send)
