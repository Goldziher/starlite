from asyncio import sleep
from collections.abc import AsyncGenerator

from litestar import Litestar, get
from litestar.response import ServerSentEvent, ServerSentEventMessage
from litestar.types import SSEData


async def my_generator() -> AsyncGenerator[SSEData, None]:
    count = 0
    while count < 10:
        await sleep(0.01)
        count += 1
        # In the generator you can yield integers, strings, bytes, dictionaries, or ServerSentEventMessage objects
        # dicts can have the following keys: data, event, id, retry, comment

        # here we yield an integer
        yield count
        # here a string
        yield str(count)
        # here bytes
        yield str(count).encode("utf-8")
        # here a dictionary
        yield {"data": 2 * count, "event": "event2", "retry": 10}
        # here a ServerSentEventMessage object
        yield ServerSentEventMessage(event="something-with-comment", retry=1000, comment="some comment")


@get(path="/count", sync_to_thread=False)
def sse_handler() -> ServerSentEvent:
    return ServerSentEvent(my_generator())


app = Litestar(route_handlers=[sse_handler])
