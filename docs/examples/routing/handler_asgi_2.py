from litestar import Response
from litestar.handlers.asgi_handlers import ASGIRouteHandler
from litestar.status_codes import HTTP_400_BAD_REQUEST
from litestar.types import Receive, Scope, Send


@ASGIRouteHandler(path="/my-asgi-app")
async def my_asgi_app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] == "http":
        if scope["method"] == "GET":
            response = Response({"hello": "world"})
            await response(scope=scope, receive=receive, send=send)
        return
    response = Response({"detail": "unsupported request"}, status_code=HTTP_400_BAD_REQUEST)
    await response(scope=scope, receive=receive, send=send)


from litestar import asgi
from litestar.types import Receive, Scope, Send


@asgi(path="/my-asgi-app")
async def my_asgi_app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] == "http":
        if scope["method"] == "GET":
            response = Response({"hello": "world"})
            await response(scope=scope, receive=receive, send=send)
        return
    response = Response({"detail": "unsupported request"}, status_code=HTTP_400_BAD_REQUEST)
    await response(scope=scope, receive=receive, send=send)
