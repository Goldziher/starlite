import time

from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.middleware import ASGIMiddleware
from litestar.types import ASGIApp, Message, Receive, Scope, Send


class ProcessTimeHeader(ASGIMiddleware):
    scopes = (ScopeType.HTTP, ScopeType.ASGI)

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        start_time = time.monotonic()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                process_time = time.monotonic() - start_time
                headers = MutableScopeHeaders.from_message(message=message)
                headers["X-Process-Time"] = str(process_time)
            await send(message)

        await next_app(scope, receive, send_wrapper)
