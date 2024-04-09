from typing import AsyncIterator

import uvicorn

from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.response import ServerSentEvent, ServerSentEventMessage
from litestar.types import SSEData


@get("/test_sse_empty")
async def handler() -> ServerSentEvent:
    async def generate() -> AsyncIterator[SSEData]:
        event = ServerSentEventMessage(event="empty")
        yield event

    return ServerSentEvent(generate())


app = Litestar(route_handlers=[handler], cors_config=CORSConfig(allow_origins=["*"]))

if __name__ == "__main__":
    uvicorn.run("sse_empty:app")
