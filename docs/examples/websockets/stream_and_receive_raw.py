import asyncio
import time
from collections.abc import AsyncGenerator

from litestar import Litestar, WebSocket, websocket
from litestar.handlers import send_websocket_stream


@websocket("/")
async def handler(socket: WebSocket) -> None:
    await socket.accept()

    async def handle_stream() -> AsyncGenerator[dict[str, float], None]:
        while True:
            yield {"time": time.time()}
            await asyncio.sleep(0.5)

    async def handle_receive() -> None:
        async for event in socket.iter_json():
            print(f"{socket.client}: {event}")

    async with asyncio.TaskGroup() as tg:
        tg.create_task(send_websocket_stream(socket=socket, stream=handle_stream()))
        tg.create_task(handle_receive())


app = Litestar([handler])
