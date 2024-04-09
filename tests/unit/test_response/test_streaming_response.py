"""A large part of the tests in this file were adapted from:

https://github.com/encode/starlette/blob/master/tests/test_responses.py And are meant to ensure our compatibility with
their API.
"""

from itertools import cycle
from typing import TYPE_CHECKING, AsyncIterator, Iterator

import anyio

from litestar.background_tasks import BackgroundTask
from litestar.response.streaming import ASGIStreamingResponse
from litestar.testing import TestClient

if TYPE_CHECKING:
    from litestar.types import Message, Receive, Scope, Send


def test_streaming_response_unknown_size() -> None:
    app = ASGIStreamingResponse(iterator=iter(["hello", "world"]))
    client = TestClient(app)
    response = client.get("/")
    assert "content-length" not in response.headers


def test_streaming_response_known_size() -> None:
    app = ASGIStreamingResponse(iterator=iter(["hello", "world"]), headers={"content-length": "10"})
    client = TestClient(app)
    response = client.get("/")
    assert response.headers["content-length"] == "10"


async def test_streaming_response_stops_if_receiving_http_disconnect_with_async_iterator(anyio_backend: str) -> None:
    streamed = 0

    disconnected = anyio.Event()

    async def receive_disconnect() -> dict:
        await disconnected.wait()
        return {"type": "http.disconnect"}

    async def send(message: "Message") -> None:
        nonlocal streamed
        if message["type"] == "http.response.body":
            streamed += len(message.get("body", b""))
            # Simulate disconnection after download has started
            if streamed >= 16:
                disconnected.set()

    async def stream_indefinitely() -> AsyncIterator[bytes]:
        while True:
            # Need a sleep for the event loop to switch to another task
            await anyio.sleep(0)
            yield b"chunk "

    response = ASGIStreamingResponse(iterator=stream_indefinitely())

    with anyio.move_on_after(1) as cancel_scope:
        await response({}, receive_disconnect, send)  # type: ignore[arg-type]
    assert not cancel_scope.cancel_called, "Content streaming should stop itself."


async def test_streaming_response_stops_if_receiving_http_disconnect_with_sync_iterator(anyio_backend: str) -> None:
    streamed = 0

    disconnected = anyio.Event()

    async def receive_disconnect() -> dict:
        await disconnected.wait()
        return {"type": "http.disconnect"}

    async def send(message: "Message") -> None:
        nonlocal streamed
        if message["type"] == "http.response.body":
            streamed += len(message.get("body", b""))
            # Simulate disconnection after download has started
            if streamed >= 16:
                disconnected.set()

    response = ASGIStreamingResponse(iterator=cycle(["1", "2", "3"]))

    with anyio.move_on_after(1) as cancel_scope:
        await response({}, receive_disconnect, send)  # type: ignore[arg-type]
    assert not cancel_scope.cancel_called, "Content streaming should stop itself."


def test_streaming_response() -> None:
    filled_by_bg_task = ""

    async def app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        async def numbers(minimum: int, maximum: int) -> AsyncIterator[str]:
            for i in range(minimum, maximum + 1):
                yield str(i)
                if i != maximum:
                    yield ", "
                await anyio.sleep(0)

        async def numbers_for_cleanup(start: int = 1, stop: int = 5) -> None:
            nonlocal filled_by_bg_task
            async for thing in numbers(start, stop):
                filled_by_bg_task += thing

        cleanup_task = BackgroundTask(numbers_for_cleanup, start=6, stop=9)
        generator = numbers(1, 5)
        response = ASGIStreamingResponse(iterator=generator, media_type="text/plain", background=cleanup_task)
        await response(scope, receive, send)

    assert not filled_by_bg_task
    client = TestClient(app)
    response = client.get("/")
    assert response.text == "1, 2, 3, 4, 5"
    assert filled_by_bg_task == "6, 7, 8, 9"


def test_streaming_response_custom_iterator() -> None:
    async def app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        class CustomAsyncIterator:
            def __init__(self) -> None:
                self._called = 0

            def __aiter__(self) -> "CustomAsyncIterator":
                return self

            async def __anext__(self) -> str:
                if self._called == 5:
                    raise StopAsyncIteration()
                self._called += 1
                return str(self._called)

        response = ASGIStreamingResponse(iterator=CustomAsyncIterator(), media_type="text/plain")
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/")
    assert response.text == "12345"


def test_streaming_response_custom_iterable() -> None:
    async def app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        class CustomAsyncIterable:
            async def __aiter__(self) -> AsyncIterator[str]:
                for i in range(5):
                    yield str(i + 1)

        response = ASGIStreamingResponse(iterator=CustomAsyncIterable(), media_type="text/plain")
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/")
    assert response.text == "12345"


def test_sync_streaming_response() -> None:
    async def app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        def numbers(minimum: int, maximum: int) -> Iterator[str]:
            for i in range(minimum, maximum + 1):
                yield str(i)
                if i != maximum:
                    yield ", "

        generator = numbers(1, 5)
        response = ASGIStreamingResponse(iterator=generator, media_type="text/plain")
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/")
    assert response.text == "1, 2, 3, 4, 5"


def test_asgi_response_encoded_headers() -> None:
    response = ASGIStreamingResponse(encoded_headers=[(b"foo", b"bar")], iterator="")
    assert response.encode_headers() == [(b"foo", b"bar"), (b"content-type", b"application/json")]
