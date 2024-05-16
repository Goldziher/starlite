from litestar import Litestar
from litestar.middleware import DefineMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send


def middleware_factory(my_arg: int, *, app: ASGIApp, my_kwarg: str) -> ASGIApp:
    async def my_middleware(scope: Scope, receive: Receive, send: Send) -> None:
        # here we can use my_arg and my_kwarg for some purpose
        await app(scope, receive, send)

    return my_middleware


app = Litestar(
    route_handlers=[...],
    middleware=[DefineMiddleware(middleware_factory, 1, my_kwarg="abc")],
)
