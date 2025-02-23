import time

from litestar import Litestar, WebSocket, get, websocket
from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.middleware import AbstractMiddleware
from litestar.types import Message, Receive, Scope, Send


class MyMiddleware(AbstractMiddleware):
    scopes = {ScopeType.HTTP}
    exclude = ["first_path", "second_path"]
    exclude_opt_key = "exclude_from_my_middleware"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        start_time = time.monotonic()

        async def send_wrapper(message: "Message") -> None:
            if message["type"] == "http.response.start":
                process_time = time.monotonic() - start_time
                headers = MutableScopeHeaders.from_message(message=message)
                headers["X-Process-Time"] = str(process_time)
            await send(message)

        await self.app(scope, receive, send_wrapper)


@websocket("/my-websocket")
async def websocket_handler(socket: WebSocket) -> None:
    """
    Websocket handler - is excluded because the middleware scopes includes 'ScopeType.HTTP'
    """
    await socket.accept()
    await socket.send_json({"hello": "websocket"})
    await socket.close()


@get("/first_path", sync_to_thread=False)
def first_handler() -> dict[str, str]:
    """Handler is excluded due to regex pattern matching "first_path"."""
    return {"hello": "first"}


@get("/second_path", sync_to_thread=False)
def second_handler() -> dict[str, str]:
    """Handler is excluded due to regex pattern matching "second_path"."""
    return {"hello": "second"}


@get("/third_path", exclude_from_my_middleware=True, sync_to_thread=False)
def third_handler() -> dict[str, str]:
    """Handler is excluded due to the opt key 'exclude_from_my_middleware' matching the middleware 'exclude_opt_key'."""
    return {"hello": "third"}


@get("/greet", sync_to_thread=False)
def not_excluded_handler() -> dict[str, str]:
    """This handler is not excluded, and thus the middleware will execute on every incoming request to it."""
    return {"hello": "world"}


app = Litestar(
    route_handlers=[
        websocket_handler,
        first_handler,
        second_handler,
        third_handler,
        not_excluded_handler,
    ],
    middleware=[MyMiddleware],
)
