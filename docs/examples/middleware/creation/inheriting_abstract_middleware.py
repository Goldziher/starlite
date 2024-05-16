from time import time
from typing import TYPE_CHECKING

from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.middleware import AbstractMiddleware

if TYPE_CHECKING:
    from litestar.types import Message, Receive, Scope, Send


class MyMiddleware(AbstractMiddleware):
    scopes = {ScopeType.HTTP}
    exclude = ["first_path", "second_path"]
    exclude_opt_key = "exclude_from_middleware"

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        start_time = time()

        async def send_wrapper(message: "Message") -> None:
            if message["type"] == "http.response.start":
                process_time = time() - start_time
                headers = MutableScopeHeaders.from_message(message=message)
                headers["X-Process-Time"] = str(process_time)
                await send(message)

        await self.app(scope, receive, send_wrapper)
