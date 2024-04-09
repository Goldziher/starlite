from __future__ import annotations

from litestar import Litestar, WebSocket, websocket_listener
from litestar.types.asgi_types import WebSocketMode


class CustomWebSocket(WebSocket):
    async def receive_data(self, mode: WebSocketMode) -> str | bytes:
        """Return fixed response for every websocket message."""
        await super().receive_data(mode=mode)
        return "Fixed response"


@websocket_listener("/")
async def handler(data: str) -> str:
    return data


app = Litestar([handler], websocket_class=CustomWebSocket)
