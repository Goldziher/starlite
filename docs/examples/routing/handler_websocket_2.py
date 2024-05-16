from litestar import WebSocket
from litestar.handlers.websocket_handlers import WebsocketRouteHandler


@WebsocketRouteHandler(path="/socket")
async def my_websocket_handler(socket: WebSocket) -> None:
    await socket.accept()
    await socket.send_json({...})
    await socket.close()
