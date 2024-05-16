from litestar.types import Receive, Scope, Send


async def my_asgi_app_function(scope: Scope, receive: Receive, send: Send) -> None:
    # do something here
    ...
