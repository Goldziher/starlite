from litestar import WebSocket, websocket


def test_resolve_websocket_class() -> None:
    @websocket()
    async def handler(socket: WebSocket) -> None:
        pass

    assert handler.resolve_websocket_class() is handler.websocket_class
