from litestar import WebSocket, websocket


@websocket(path="/socket")
async def my_websocket_handler(socket: WebSocket) -> None:
    await socket.accept()
    await socket.send_json({...})
    await socket.close()
