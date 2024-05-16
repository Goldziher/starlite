from litestar import Litestar
from litestar.handlers.websocket_handlers import websocket_listener


@websocket_listener("/")
async def handler(data: str) -> str:
    return data


app = Litestar([handler])
