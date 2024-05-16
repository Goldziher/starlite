import time

from litestar.datastructures import MutableScopeHeaders
from litestar.middleware.base import MiddlewareProtocol
from litestar.types import ASGIApp, Message, Receive, Scope, Send


class ProcessTimeHeader(MiddlewareProtocol):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            start_time = time.time()

            async def send_wrapper(message: Message) -> None:
                if message["type"] == "http.response.start":
                    process_time = time.time() - start_time
                    headers = MutableScopeHeaders.from_message(message=message)
                    headers["X-Process-Time"] = str(process_time)
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
