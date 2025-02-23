from collections.abc import AsyncIterator, Iterator

import anyio
import pytest
from httpx_sse import ServerSentEvent as HTTPXServerSentEvent
from httpx_sse import aconnect_sse

from litestar import get
from litestar.exceptions import ImproperlyConfiguredException
from litestar.response import ServerSentEvent
from litestar.response.sse import ServerSentEventMessage
from litestar.testing import create_async_test_client
from litestar.types import SSEData


async def test_sse_steaming_response() -> None:
    @get(
        path="/test",
    )
    def handler() -> ServerSentEvent:
        def numbers(minimum: int, maximum: int) -> Iterator[str]:
            for i in range(minimum, maximum + 1):
                yield str(i)

        generator = numbers(1, 5)

        return ServerSentEvent(content=generator, event_id="123", event_type="special", retry_duration=1000)

    async with create_async_test_client(handler) as client:
        async with aconnect_sse(client, "GET", f"{client.base_url}/test") as event_source:
            events = [sse async for sse in event_source.aiter_sse()]
            assert len(events) == 5
            for idx, sse in enumerate(events, start=1):
                assert sse.event == "special"
                assert sse.data == str(idx)
                assert sse.id == "123"
                assert sse.retry == 1000


@pytest.mark.parametrize(
    "input,expected_events",
    [
        ("string", [HTTPXServerSentEvent(event="special", data=str(i), id="123", retry=1000) for i in range(1, 6)]),
        ("bytes", [HTTPXServerSentEvent(event="special", data=str(i), id="123", retry=1000) for i in range(1, 6)]),
        ("integer", [HTTPXServerSentEvent(event="special", data=str(i), id="123", retry=1000) for i in range(1, 6)]),
        ("dict1", [HTTPXServerSentEvent(event="special", data=str(i), id="123", retry=1000) for i in range(1, 6)]),
        (
            "dict2",
            [
                HTTPXServerSentEvent(
                    event=e, data=str(i) if e == "event1" else str(2 * i), id="123", retry=1000 if e == "event1" else 10
                )
                for i in range(1, 6)
                for e in ["event1", "event2"]
            ],
        ),
        ("obj", [HTTPXServerSentEvent(event="special", data=str(i), id="123", retry=1000) for i in range(1, 6)]),
        ("empty", [HTTPXServerSentEvent(event="something-empty", id="123", retry=1000) for i in range(1, 6)]),
        ("comment", [HTTPXServerSentEvent(event="something-with-comment", id="123", retry=1000) for i in range(1, 6)]),
    ],
)
async def test_various_sse_inputs(input: str, expected_events: list[HTTPXServerSentEvent]) -> None:
    @get("/testme")
    async def handler() -> ServerSentEvent:
        async def numbers() -> AsyncIterator[SSEData]:
            for i in range(1, 6):
                await anyio.sleep(0.001)
                if input == "integer":
                    yield i
                elif input == "string":
                    yield str(i)
                elif input == "bytes":
                    yield str(i).encode("utf-8")
                elif input == "dict1":
                    yield {"data": i, "event": "special", "retry": 1000}
                elif input == "dict2":
                    yield {"data": i, "event": "event1", "retry": 1000}
                    yield {"data": 2 * i, "event": "event2", "retry": 10}
                elif input == "obj":
                    yield ServerSentEventMessage(data=i, event="special", retry=1000)
                elif input == "empty":
                    yield ServerSentEventMessage(event="something-empty", retry=1000)
                elif input == "comment":
                    yield ServerSentEventMessage(event="something-with-comment", retry=1000, comment="some comment")

        return ServerSentEvent(numbers(), event_type="special", event_id="123", retry_duration=1000)

    async with create_async_test_client(handler) as client:
        async with aconnect_sse(client, "GET", f"{client.base_url}/testme") as event_source:
            events = [sse async for sse in event_source.aiter_sse()]
            assert len(events) == len(expected_events)
            for i in range(len(expected_events)):
                assert events[i].event == expected_events[i].event
                assert events[i].data == expected_events[i].data
                assert events[i].id == expected_events[i].id
                assert events[i].retry == expected_events[i].retry


def test_invalid_content_type_raises() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        ServerSentEvent(content=object())  # type: ignore[arg-type]
