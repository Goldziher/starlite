from litestar import get
from litestar.types import ASGIApp, Receive, Scope, Send


@get("/")
def handler() -> ASGIApp:
    async def my_asgi_app(scope: Scope, receive: Receive, send: Send) -> None: ...

    return my_asgi_app
