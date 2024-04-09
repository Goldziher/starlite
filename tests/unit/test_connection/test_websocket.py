"""
Some tests in this file were adapted from: https://github.com/encode/starlette/blob/master/tests/test_websockets.py And
were meant to ensure our compatibility with their API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncGenerator, Literal
from unittest.mock import MagicMock

import anyio
import pytest

from litestar.connection import WebSocket
from litestar.datastructures.headers import Headers
from litestar.exceptions import WebSocketDisconnect, WebSocketException
from litestar.handlers.websocket_handlers import websocket
from litestar.status_codes import WS_1001_GOING_AWAY
from litestar.testing import TestClient, create_test_client
from litestar.types.asgi_types import WebSocketMode
from litestar.utils.compat import async_next

if TYPE_CHECKING:
    from litestar.types import Receive, Scope, Send


@pytest.mark.parametrize("mode", ["text", "binary"])
def test_websocket_send_receive_json(mode: Literal["text", "binary"]) -> None:
    @websocket(path="/")
    async def websocket_handler(socket: WebSocket) -> None:
        await socket.accept()
        recv = await socket.receive_json(mode=mode)
        await socket.send_json({"message": recv}, mode=mode)
        await socket.close()

    with create_test_client(route_handlers=[websocket_handler]).websocket_connect("/") as ws:
        ws.send_json({"hello": "world"}, mode=mode)
        data = ws.receive_json(mode=mode)
        assert data == {"message": {"hello": "world"}}


def test_route_handler_property() -> None:
    value: Any = {}

    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        value["handler"] = socket.route_handler
        await socket.close()

    with create_test_client(route_handlers=[handler]).websocket_connect("/"):
        assert str(value["handler"]) == str(handler)


@pytest.mark.parametrize(
    "headers", [[(b"test", b"hello-world")], {"test": "hello-world"}, Headers(headers={"test": "hello-world"})]
)
async def test_accept_set_headers(headers: Any) -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept(headers=headers)
        await socket.send_text("abc")
        await socket.close()

    with create_test_client(route_handlers=[handler]).websocket_connect("/") as ws:
        assert dict(ws.scope["headers"])[b"test"] == b"hello-world"


async def test_custom_request_class() -> None:
    value: Any = {}

    class MyWebSocket(WebSocket[Any, Any, Any]):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.scope["called"] = True  # type: ignore[typeddict-unknown-key]

    @websocket("/", signature_types=[MyWebSocket])
    async def handler(socket: MyWebSocket) -> None:
        value["called"] = socket.scope.get("called")
        await socket.accept()
        await socket.close()

    with create_test_client(route_handlers=[handler], websocket_class=MyWebSocket).websocket_connect("/"):
        assert value["called"]


def test_websocket_url() -> None:
    @websocket("/123")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        await socket.send_json({"url": str(socket.url)})
        await socket.close()

    with create_test_client(handler).websocket_connect("/123?a=abc") as ws:
        assert ws.receive_json() == {"url": "ws://testserver/123?a=abc"}


def test_websocket_binary_json() -> None:
    @websocket("/123")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        message = await socket.receive_json(mode="binary")
        await socket.send_json(message, mode="binary")
        await socket.close()

    with create_test_client(handler).websocket_connect("/123?a=abc") as ws:
        ws.send_json({"test": "data"}, mode="binary")
        assert ws.receive_json(mode="binary") == {"test": "data"}


def test_websocket_query_params() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        query_params = dict(socket.query_params)
        await socket.accept()
        await socket.send_json({"params": query_params})
        await socket.close()

    with create_test_client(handler).websocket_connect("/?a=abc&b=456") as ws:
        assert ws.receive_json() == {"params": {"a": "abc", "b": "456"}}


def test_websocket_headers() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        headers = dict(socket.headers)
        await socket.accept()
        await socket.send_json({"headers": headers})
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        expected_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "connection": "upgrade",
            "host": "testserver",
            "user-agent": "testclient",
            "sec-websocket-key": "testserver==",
            "sec-websocket-version": "13",
        }
        assert ws.receive_json() == {"headers": expected_headers}


def test_websocket_port() -> None:
    @websocket("/123")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        await socket.send_json({"port": socket.url.port})
        await socket.close()

    with create_test_client(handler).websocket_connect("ws://example.com:123/123?a=abc") as ws:
        assert ws.receive_json() == {"port": 123}


def test_websocket_send_and_receive_text() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        data = await socket.receive_text()
        await socket.send_text(f"Message was: {data}")
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        ws.send_text("Hello, world!")
        assert ws.receive_text() == "Message was: Hello, world!"


def test_websocket_send_and_receive_bytes() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        data = await socket.receive_bytes()
        await socket.send_bytes(b"Message was: " + data)
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        ws.send_bytes(b"Hello, world!")
        assert ws.receive_bytes() == b"Message was: Hello, world!"


def test_websocket_send_and_receive_json() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        data = await socket.receive_json()
        await socket.send_json({"message": data})
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        ws.send_json({"hello": "world"})
        assert ws.receive_json() == {"message": {"hello": "world"}}


def test_send_msgpack() -> None:
    test_data = {"message": "hello, world"}

    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        await socket.send_msgpack(test_data)
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        data = ws.receive_msgpack(timeout=1)
        assert data == test_data


def test_receive_msgpack() -> None:
    test_data = {"message": "hello, world"}
    callback = MagicMock()

    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        data = await socket.receive_msgpack()
        callback(data)
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        ws.send_msgpack(test_data)

    callback.assert_called_once_with(test_data)


async def consume_gen(generator: AsyncGenerator[Any, Any], count: int, timeout: int = 1) -> list[Any]:
    async def consumer() -> list[Any]:
        result = []
        for _ in range(count):
            result.append(await async_next(generator))
        return result

    with anyio.fail_after(timeout):
        return await consumer()


@pytest.mark.parametrize("mode,data", [("text", ["foo", "bar"]), ("binary", [b"foo", b"bar"])])
def test_iter_data(mode: WebSocketMode, data: list[str | bytes]) -> None:
    values = []

    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        values.extend(await consume_gen(socket.iter_data(mode=mode), 2))
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        for message in data:
            ws.send(message, mode=mode)

    assert values == data


@pytest.mark.parametrize("mode", ["text", "binary"])
def test_iter_json(mode: WebSocketMode) -> None:
    messages = [{"data": "foo"}, {"data": "bar"}]
    values = []

    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        values.extend(await consume_gen(socket.iter_json(mode=mode), 2))
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        for message in messages:
            ws.send_json(message, mode=mode)

    assert values == messages


def test_iter_msgpack() -> None:
    messages = [{"data": "foo"}, {"data": "bar"}]
    values = []

    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        values.extend(await consume_gen(socket.iter_msgpack(), 2))
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        for message in messages:
            ws.send_msgpack(message)

    assert values == messages


def test_websocket_concurrency_pattern() -> None:
    stream_send, stream_receive = anyio.create_memory_object_stream()  # type: ignore[var-annotated]

    async def reader(socket: WebSocket[Any, Any, Any]) -> None:
        async with stream_send:
            json_data = await socket.receive_json()
            await stream_send.send(json_data)

    async def writer(socket: WebSocket[Any, Any, Any]) -> None:
        async with stream_receive:
            async for message in stream_receive:
                await socket.send_json(message)

    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(reader, socket)
            await writer(socket)
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        ws.send_json({"hello": "world"})
        data = ws.receive_json()
        assert data == {"hello": "world"}


def test_client_close() -> None:
    close_code = None

    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        nonlocal close_code
        await socket.accept()
        try:
            await socket.receive_text()
        except WebSocketException as exc:
            close_code = exc.code

    with create_test_client(handler).websocket_connect("/") as ws:
        ws.close(code=WS_1001_GOING_AWAY)
    assert close_code == WS_1001_GOING_AWAY


def test_application_close() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        await socket.close(WS_1001_GOING_AWAY)

    with create_test_client(handler).websocket_connect("/") as ws, pytest.raises(WebSocketDisconnect) as exc:
        ws.receive_text()
    assert exc.value.code == WS_1001_GOING_AWAY


def test_rejected_connection() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.close(WS_1001_GOING_AWAY)

    with pytest.raises(WebSocketDisconnect) as exc, create_test_client(handler).websocket_connect("/"):
        pass
    assert exc.value.code == WS_1001_GOING_AWAY


def test_subprotocol() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        assert socket.scope["subprotocols"] == ["soap", "wamp"]
        await socket.accept(subprotocols="wamp")
        await socket.close()

    with create_test_client(handler).websocket_connect("/", subprotocols=["soap", "wamp"]) as ws:
        assert ws.accepted_subprotocol == "wamp"


def test_additional_headers() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept(headers=[(b"additional", b"header")])
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        assert ws.extra_headers == [(b"additional", b"header")]


def test_no_additional_headers() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        await socket.close()

    with create_test_client(handler).websocket_connect("/") as ws:
        assert ws.extra_headers == []


def test_websocket_exception() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        raise RuntimeError

    with pytest.raises(RuntimeError), TestClient(app).websocket_connect("/123?a=abc"):
        pass


def test_duplicate_disconnect() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        socket = WebSocket[Any, Any, Any](scope, receive=receive, send=send)
        await socket.accept()
        message = await socket.receive()
        assert message["type"] == "websocket.disconnect"
        await socket.receive()

    with pytest.raises(WebSocketException), TestClient(app).websocket_connect("/") as websocket:
        websocket.close()


def test_websocket_close_reason() -> None:
    @websocket("/")
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        await socket.close(code=WS_1001_GOING_AWAY, reason="Going Away")

    with create_test_client(handler).websocket_connect("/") as ws, pytest.raises(WebSocketDisconnect) as exc:
        ws.receive_text()
        assert exc.value.code == WS_1001_GOING_AWAY
        assert exc.value.detail == "Going Away"


def test_receive_text_before_accept() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        socket = WebSocket[Any, Any, Any](scope, receive=receive, send=send)
        await socket.receive_text()

    with pytest.raises(WebSocketException), TestClient(app).websocket_connect("/"):
        pass


def test_receive_bytes_before_accept() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        socket = WebSocket[Any, Any, Any](scope, receive=receive, send=send)
        await socket.receive_bytes()

    with pytest.raises(WebSocketException), TestClient(app).websocket_connect("/"):
        pass


def test_receive_json_before_accept() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        socket = WebSocket[Any, Any, Any](scope, receive=receive, send=send)
        await socket.receive_json()

    with pytest.raises(WebSocketException), TestClient(app).websocket_connect("/"):
        pass
