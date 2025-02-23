from __future__ import annotations

import asyncio
import dataclasses
from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest

from litestar import Controller, Litestar, WebSocket
from litestar.dto import DataclassDTO, dto_field
from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers.websocket_handlers import websocket_stream
from litestar.testing import create_test_client


def test_websocket_stream() -> None:
    @websocket_stream("/")
    async def handler(socket: WebSocket) -> AsyncGenerator[str, None]:
        yield "foo"
        yield "bar"

    with create_test_client([handler]) as client, client.websocket_connect("/") as ws:
        assert ws.receive_text(timeout=0.1) == "foo"
        assert ws.receive_text(timeout=0.1) == "bar"


def test_websocket_stream_in_controller() -> None:
    class MyController(Controller):
        @websocket_stream("/")
        async def handler(self, socket: WebSocket) -> AsyncGenerator[str, None]:
            yield "foo"

    with create_test_client([MyController]) as client, client.websocket_connect("/") as ws:
        assert ws.receive_text(timeout=0.1) == "foo"


def test_websocket_stream_without_socket() -> None:
    @websocket_stream("/")
    async def handler() -> AsyncGenerator[str, None]:
        yield "foo"

    with create_test_client([handler]) as client, client.websocket_connect("/") as ws:
        assert ws.receive_text(timeout=0.1) == "foo"


def test_websocket_stream_dependency_injection() -> None:
    async def provide_hello() -> str:
        return "hello"

    # ensure we can inject dependencies
    @websocket_stream("/1", dependencies={"greeting": provide_hello})
    async def handler_one(greeting: str) -> AsyncGenerator[str, None]:
        yield greeting

    # ensure dependency injection also works with 'socket' present
    @websocket_stream("/2", dependencies={"greeting": provide_hello})
    async def handler_two(socket: WebSocket, greeting: str) -> AsyncGenerator[str, None]:
        yield greeting

    with create_test_client([handler_one, handler_two]) as client:
        with client.websocket_connect("/1") as ws:
            assert ws.receive_text(timeout=0.1) == "hello"

        with client.websocket_connect("/2") as ws:
            assert ws.receive_text(timeout=0.1) == "hello"


def test_websocket_stream_dependencies_cleaned_up_after_stream_close() -> None:
    mock = MagicMock()

    async def dep() -> AsyncGenerator[str, None]:
        yield "foo"
        mock()

    @websocket_stream(
        "/",
        dependencies={"message": dep},
        listen_for_disconnect=False,
    )
    async def handler(socket: WebSocket, message: str) -> AsyncGenerator[str, None]:
        yield "one"
        await socket.receive_text()
        yield message

    with create_test_client([handler]) as client, client.websocket_connect("/") as ws:
        assert ws.receive_text(timeout=0.1) == "one"
        assert mock.call_count == 0
        ws.send_text("")
        assert ws.receive_text(timeout=0.1) == "foo"

    assert mock.call_count == 1


def test_websocket_stream_handle_disconnect() -> None:
    @websocket_stream("/")
    async def handler() -> AsyncGenerator[str, None]:
        while True:
            yield "foo"
            # sleep for longer than our read-timeout to ensure we're disconnecting prematurely
            await asyncio.sleep(1)

    with create_test_client([handler]) as client, client.websocket_connect("/") as ws:
        assert ws.receive_text(timeout=0.1) == "foo"

    with create_test_client([handler]) as client, client.websocket_connect("/") as ws:
        # ensure we still disconnect even after receiving some data
        ws.send_text("")
        assert ws.receive_text(timeout=0.1) == "foo"


def test_websocket_stream_send_json() -> None:
    @websocket_stream("/")
    async def handler() -> AsyncGenerator[dict[str, str], None]:
        yield {"hello": "there"}
        yield {"and": "goodbye"}

    with create_test_client([handler]) as client, client.websocket_connect("/") as ws:
        assert ws.receive_json(timeout=0.1) == {"hello": "there"}
        assert ws.receive_json(timeout=0.1) == {"and": "goodbye"}


def test_websocket_stream_send_json_with_dto() -> None:
    @dataclasses.dataclass
    class Event:
        id: int = dataclasses.field(metadata=dto_field("private"))
        content: str

    @websocket_stream("/", return_dto=DataclassDTO[Event])
    async def handler() -> AsyncGenerator[Event, None]:
        yield Event(id=1, content="hello")

    with create_test_client([handler], signature_types=[Event]) as client, client.websocket_connect("/") as ws:
        assert ws.receive_json(timeout=0.1) == {"content": "hello"}


def test_raises_if_stream_fn_does_not_return_async_generator() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @websocket_stream("/")  # type: ignore[arg-type]
        def foo() -> Generator[bytes, None, None]:
            yield b""

        Litestar([foo])

    with pytest.raises(ImproperlyConfiguredException):

        @websocket_stream("/")  # type: ignore[arg-type]
        def foo() -> bytes:
            return b""

        Litestar([foo])
