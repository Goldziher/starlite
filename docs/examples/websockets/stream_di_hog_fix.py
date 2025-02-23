import asyncio
from collections.abc import AsyncGenerator

from app.lib import ping_external_resource
from litestar import Litestar, websocket_stream

RESOURCE_LOCK = asyncio.Lock()


@websocket_stream("/")
async def ping() -> AsyncGenerator[float, None]:
    while True:
        async with RESOURCE_LOCK:
            alive = await ping_external_resource()
        yield alive
        await asyncio.sleep(1)


app = Litestar([ping])
