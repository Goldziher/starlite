from litestar.types import Receive, Scope, Send


class ASGIApp:
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # do something here
        ...
