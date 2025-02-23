import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any

from litestar import Litestar, WebSocket, websocket_listener
from litestar.handlers import send_websocket_stream


async def listener_lifespan(socket: WebSocket) -> None:
    async def handle_stream() -> AsyncGenerator[dict[str, float], None]:
        while True:
            yield {"time": time.time()}
            await asyncio.sleep(0.5)

    task = asyncio.create_task(send_websocket_stream(socket=socket, stream=handle_stream()))
    yield
    task.cancel()
    await task


@websocket_listener("/", connection_lifespan=listener_lifespan)
def handler(socket: WebSocket, data: Any) -> None:
    print(f"{socket.client}: {data}")


app = Litestar([handler])
