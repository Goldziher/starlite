from asyncio import sleep
from collections.abc import AsyncGenerator
from datetime import datetime

from litestar import Litestar, get
from litestar.response import Stream
from litestar.serialization import encode_json


async def my_generator() -> AsyncGenerator[bytes, None]:
    while True:
        await sleep(0.01)
        yield encode_json({"current_time": datetime.now()})


@get(path="/time")
def stream_time() -> Stream:
    return Stream(my_generator())


app = Litestar(route_handlers=[stream_time])
