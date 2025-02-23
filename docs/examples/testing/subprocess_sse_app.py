"""
Assemble components into an app that shall be tested
"""

from collections.abc import AsyncGenerator

from litestar import Litestar, get
from litestar.response import ServerSentEvent
from litestar.types import SSEData


async def generator(topic: str) -> AsyncGenerator[SSEData, None]:
    count = 0
    while count < 2:
        yield topic
        count += 1


@get("/notify/{topic:str}")
async def get_notified(topic: str) -> ServerSentEvent:
    return ServerSentEvent(generator(topic), event_type="Notifier")


app = Litestar(route_handlers=[get_notified])
