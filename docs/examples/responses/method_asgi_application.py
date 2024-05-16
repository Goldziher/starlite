from litestar.types import Receive, Scope, Send


class MyClass:
    async def my_asgi_app_method(self, scope: Scope, receive: Receive, send: Send) -> None:
        # do something here
        ...
