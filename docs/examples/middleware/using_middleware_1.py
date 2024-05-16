from litestar.types import ASGIApp, Receive, Scope, Send


def middleware_factory(app: ASGIApp) -> ASGIApp:
    async def my_middleware(scope: Scope, receive: Receive, send: Send) -> None:
        # do something here
        await app(scope, receive, send)

    return my_middleware
