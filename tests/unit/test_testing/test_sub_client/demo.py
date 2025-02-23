"""
Assemble components into an app that shall be tested
"""

import asyncio
from collections.abc import AsyncIterator

from litestar import Litestar, get
from litestar.response import ServerSentEvent


@get("/notify/{topic:str}")
async def get_notified(topic: str) -> ServerSentEvent:
    async def generator() -> AsyncIterator[str]:
        yield topic
        while True:
            await asyncio.sleep(0.1)

    return ServerSentEvent(generator(), event_type="Notifier")


def create_test_app() -> Litestar:
    return Litestar(
        route_handlers=[get_notified],
    )


app = create_test_app()
