from litestar import WebSocket, websocket


@websocket("/")
async def handler(socket: WebSocket) -> None:
    await socket.accept()
    async for message in socket.iter_data(mode):
        await socket.send_msgpack(message)
