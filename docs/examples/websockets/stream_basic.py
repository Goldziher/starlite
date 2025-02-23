import asyncio
import time
from collections.abc import AsyncGenerator

from litestar import Litestar, websocket_stream


@websocket_stream("/")
async def ping() -> AsyncGenerator[float, None]:
    while True:
        yield time.time()
        await asyncio.sleep(0.5)


app = Litestar([ping])
