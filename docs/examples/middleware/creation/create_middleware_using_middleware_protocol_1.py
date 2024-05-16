from typing import Any, Protocol

from litestar.types import ASGIApp, Receive, Scope, Send


class MiddlewareProtocol(Protocol):
    def __init__(self, app: ASGIApp, **kwargs: Any) -> None: ...

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None: ...
