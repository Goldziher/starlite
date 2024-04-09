"""A large part of the tests in this file were adapted from:

https://github.com/encode/starlette/blob/master/tests/test_requests.py. And are meant to ensure our compatibility with
their API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Generator
from unittest.mock import patch

import pytest

from litestar import MediaType, Request, asgi, get
from litestar.connection.base import empty_send
from litestar.datastructures import Address, Cookie
from litestar.exceptions import (
    InternalServerException,
    LitestarException,
    LitestarWarning,
    SerializationException,
)
from litestar.middleware import MiddlewareProtocol
from litestar.response.base import ASGIResponse
from litestar.serialization import encode_json, encode_msgpack
from litestar.static_files.config import StaticFilesConfig
from litestar.testing import TestClient, create_test_client

if TYPE_CHECKING:
    from pathlib import Path

    from litestar.types import ASGIApp, Receive, Scope, Send


@get("/", sync_to_thread=False)
def _route_handler() -> None:
    pass


@pytest.fixture(name="scope")
def scope_fixture(create_scope: Callable[..., Scope]) -> Scope:
    return create_scope(type="http", route_handler=_route_handler)


async def test_request_empty_body_to_json(anyio_backend: str, scope: Scope) -> None:
    with patch.object(Request, "body", return_value=b""):
        request_empty_payload: Request = Request(scope=scope)
        request_json = await request_empty_payload.json()
        assert request_json is None


async def test_request_invalid_body_to_json(anyio_backend: str, scope: Scope) -> None:
    with patch.object(Request, "body", return_value=b"invalid"), pytest.raises(SerializationException):
        request_empty_payload: Request = Request(scope=scope)
        await request_empty_payload.json()


async def test_request_valid_body_to_json(anyio_backend: str, scope: Scope) -> None:
    with patch.object(Request, "body", return_value=b'{"test": "valid"}'):
        request_empty_payload: Request = Request(scope=scope)
        request_json = await request_empty_payload.json()
        assert request_json == {"test": "valid"}


async def test_request_empty_body_to_msgpack(anyio_backend: str, scope: Scope) -> None:
    with patch.object(Request, "body", return_value=b""):
        request_empty_payload: Request = Request(scope=scope)
        request_msgpack = await request_empty_payload.msgpack()
        assert request_msgpack is None


async def test_request_invalid_body_to_msgpack(anyio_backend: str, scope: Scope) -> None:
    with patch.object(Request, "body", return_value=b"invalid"), pytest.raises(SerializationException):
        request_empty_payload: Request = Request(scope=scope)
        await request_empty_payload.msgpack()


async def test_request_valid_body_to_msgpack(anyio_backend: str, scope: Scope) -> None:
    with patch.object(Request, "body", return_value=encode_msgpack({"test": "valid"})):
        request_empty_payload: Request = Request(scope=scope)
        request_msgpack = await request_empty_payload.msgpack()
        assert request_msgpack == {"test": "valid"}


def test_request_url_for() -> None:
    @get(path="/proxy", name="proxy")
    def proxy() -> None:
        pass

    @get(path="/test", signature_namespace={"dict": Dict})
    def root(request: Request) -> dict[str, str]:
        return {"url": request.url_for("proxy")}

    @get(path="/test-none", signature_namespace={"dict": Dict})
    def test_none(request: Request) -> dict[str, str]:
        return {"url": request.url_for("none")}

    with create_test_client(route_handlers=[proxy, root, test_none]) as client:
        response = client.get("/test")
        assert response.json() == {"url": "http://testserver.local/proxy"}

        response = client.get("/test-none")
        assert response.status_code == 500


def test_request_asset_url(tmp_path: Path) -> None:
    @get(path="/resolver", signature_namespace={"dict": Dict})
    def resolver(request: Request) -> dict[str, str]:
        return {"url": request.url_for_static_asset("js", "main.js")}

    @get(path="/resolver-none", signature_namespace={"dict": Dict})
    def resolver_none(request: Request) -> dict[str, str]:
        return {"url": request.url_for_static_asset("none", "main.js")}

    with create_test_client(
        route_handlers=[resolver, resolver_none],
        static_files_config=[StaticFilesConfig(path="/static/js", directories=[tmp_path], name="js")],
    ) as client:
        response = client.get("/resolver")
        assert response.json() == {"url": "http://testserver.local/static/js/main.js"}

        response = client.get("/resolver-none")
        assert response.status_code == 500


def test_route_handler_property() -> None:
    value: Any = {}

    @get("/")
    def handler(request: Request) -> None:
        value["handler"] = request.route_handler

    with create_test_client(route_handlers=[handler]) as client:
        client.get("/")
        assert str(value["handler"]) == str(handler)


def test_custom_request_class() -> None:
    value: Any = {}

    class MyRequest(Request):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.scope["called"] = True  # type: ignore[typeddict-unknown-key]

    @get("/", signature_types=[MyRequest])
    def handler(request: MyRequest) -> None:
        value["called"] = request.scope.get("called")

    with create_test_client(route_handlers=[handler], request_class=MyRequest) as client:
        client.get("/")
        assert value["called"]


def test_request_url() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        data = {"method": request.method, "url": str(request.url)}
        response = ASGIResponse(body=encode_json(data))
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/123?a=abc")
    assert response.json() == {"method": "GET", "url": "http://testserver.local/123?a=abc"}

    response = client.get("https://example.org:123/")
    assert response.json() == {"method": "GET", "url": "https://example.org:123/"}


def test_request_query_params() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        params = dict(request.query_params)
        response = ASGIResponse(body=encode_json({"params": params}))
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/?a=123&b=456")
    assert response.json() == {"params": {"a": "123", "b": "456"}}


def test_request_headers() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        headers = dict(request.headers)
        response = ASGIResponse(body=encode_json({"headers": headers}))
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/", headers={"host": "example.org"})
    assert response.json() == {
        "headers": {
            "host": "example.org",
            "user-agent": "testclient",
            "accept-encoding": "gzip, deflate, br",
            "accept": "*/*",
            "connection": "keep-alive",
        }
    }


def test_request_accept_header() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        response = ASGIResponse(body=encode_json({"accepted_types": list(request.accept)}))
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/", headers={"Accept": "text/plain, application/xml;q=0.7, text/html;p=test"})
    assert response.json() == {"accepted_types": ["text/html;p=test", "text/plain", "application/xml;q=0.7"]}


@pytest.mark.parametrize(
    "scope_values,expected_client",
    (
        ({"type": "http", "route_handler": _route_handler, "client": ["client", 42]}, Address("client", 42)),
        ({"type": "http", "route_handler": _route_handler, "client": None}, None),
        ({"type": "http", "route_handler": _route_handler}, None),
    ),
)
def test_request_client(
    scope_values: dict[str, Any], expected_client: Address | None, create_scope: Callable[..., Scope]
) -> None:
    scope = create_scope()
    scope.update(scope_values)  # type: ignore[typeddict-item]
    if "client" not in scope_values:
        del scope["client"]  # type: ignore[misc]
    client = Request[Any, Any, Any](scope).client
    assert client == expected_client


def test_request_body() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        body = await request.body()
        response = ASGIResponse(body=encode_json({"body": body.decode()}))
        await response(scope, receive, send)

    client = TestClient(app)

    response = client.get("/")
    assert response.json() == {"body": ""}

    response = client.post("/", json={"a": "123"})
    assert response.json() == {"body": '{"a": "123"}'}

    response = client.post("/", content="abc")
    assert response.json() == {"body": "abc"}


def test_request_stream() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        body = b""
        async for chunk in request.stream():
            body += chunk
        response = ASGIResponse(body=encode_json({"body": body.decode()}))
        await response(scope, receive, send)

    client = TestClient(app)

    response = client.get("/")
    assert response.json() == {"body": ""}

    response = client.post("/", json={"a": "123"})
    assert response.json() == {"body": '{"a": "123"}'}

    response = client.post("/", content="abc")
    assert response.json() == {"body": "abc"}


def test_request_form_urlencoded() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        form = await request.form()
        response = ASGIResponse(body=encode_json({"form": dict(form)}))
        await response(scope, receive, send)

    client = TestClient(app)

    response = client.post("/", data={"abc": "123 @"})
    assert response.json() == {"form": {"abc": "123 @"}}


def test_request_body_then_stream() -> None:
    async def app(scope: Any, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        body = await request.body()
        chunks = b""
        async for chunk in request.stream():
            chunks += chunk
        response = ASGIResponse(body=encode_json({"body": body.decode(), "stream": chunks.decode()}))
        await response(scope, receive, send)

    client = TestClient(app)

    response = client.post("/", content="abc")
    assert response.json() == {"body": "abc", "stream": "abc"}


def test_request_stream_then_body() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        chunks = b""
        async for chunk in request.stream():
            chunks += chunk
        try:
            body = await request.body()
        except InternalServerException:
            body = b"<stream consumed>"
        response = ASGIResponse(body=encode_json({"body": body.decode(), "stream": chunks.decode()}))
        await response(scope, receive, send)

    client = TestClient(app)

    response = client.post("/", content="abc")
    assert response.json() == {"body": "<stream consumed>", "stream": "abc"}


def test_request_json() -> None:
    @asgi("/")
    async def handler(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        data = await request.json()
        response = ASGIResponse(body=encode_json({"json": data}))
        await response(scope, receive, send)

    with create_test_client(handler) as client:
        response = client.post("/", json={"a": "123"})
        assert response.json() == {"json": {"a": "123"}}


def test_request_raw_path() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        path = str(request.scope["path"])
        raw_path = str(request.scope["raw_path"])
        response = ASGIResponse(body=f"{path}, {raw_path}".encode(), media_type=MediaType.TEXT)
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/he%2Fllo")
    assert response.text == "/he/llo, b'/he%2Fllo'"


def test_request_without_setting_receive() -> None:
    """If Request is instantiated without the 'receive' channel, then .body() is not available."""

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope)
        try:
            data = await request.json()
        except RuntimeError:
            data = "Receive channel not available"
        response = ASGIResponse(body=encode_json({"json": data}))
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.post("/", json={"a": "123"})
    assert response.json() == {"json": "Receive channel not available"}


async def test_request_disconnect(create_scope: Callable[..., Scope]) -> None:
    """If a client disconnect occurs while reading request body then InternalServerException should be raised."""

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        await request.body()

    async def receiver() -> dict:
        return {"type": "http.disconnect"}

    with pytest.raises(InternalServerException):
        await app(
            create_scope(type="http", route_handler=_route_handler, method="POST", path="/"),
            receiver,  # type: ignore[arg-type]
            empty_send,
        )


def test_request_state() -> None:
    @get("/", signature_namespace={"dict": Dict})
    def handler(request: Request[Any, Any, Any]) -> dict[Any, Any]:
        request.state.test = 1
        assert request.state.test == 1
        return request.state.dict()  # type: ignore[no-any-return]

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json()["test"] == 1


def test_request_cookies() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        mycookie = request.cookies.get("mycookie")
        if mycookie:
            asgi_response = ASGIResponse(body=mycookie.encode("utf-8"), media_type="text/plain")
        else:
            asgi_response = ASGIResponse(
                body=b"Hello, world!",
                media_type="text/plain",
                cookies=[Cookie(key="mycookie", value="Hello, cookies!")],
            )

        await asgi_response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/")
    assert response.text == "Hello, world!"
    response = client.get("/")
    assert response.text == "Hello, cookies!"


def test_chunked_encoding() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope, receive)
        body = await request.body()
        response = ASGIResponse(body=encode_json({"body": body.decode()}))
        await response(scope, receive, send)

    client = TestClient(app)

    def post_body() -> Generator[bytes, None, None]:
        yield b"foo"
        yield b"bar"

    response = client.post("/", content=post_body())
    assert response.json() == {"body": "foobar"}


def test_request_send_push_promise() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        # the server is push-enabled
        scope["extensions"]["http.response.push"] = {}  # type: ignore[index]

        request = Request[Any, Any, Any](scope, receive, send)
        await request.send_push_promise("/style.css")

        response = ASGIResponse(body=encode_json({"json": "OK"}))
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/")
    assert response.json() == {"json": "OK"}


def test_request_send_push_promise_without_push_extension() -> None:
    """If server does not support the `http.response.push` extension,

    .send_push_promise() does nothing.
    """

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope)

        with pytest.warns(LitestarWarning, match="Attempted to send a push promise"):
            await request.send_push_promise("/style.css")

        response = ASGIResponse(body=encode_json({"json": "OK"}))
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/")
    assert response.json() == {"json": "OK"}


def test_request_send_push_promise_without_push_extension_raises() -> None:
    """If server does not support the `http.response.push` extension,

    .send_push_promise() does nothing.
    """

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request[Any, Any, Any](scope)

        with pytest.raises(LitestarException, match="Attempted to send a push promise"):
            await request.send_push_promise("/style.css", raise_if_unavailable=True)

        response = ASGIResponse(body=encode_json({"json": "OK"}))
        await response(scope, receive, send)

    TestClient(app).get("/")


def test_request_send_push_promise_without_setting_send() -> None:
    """If Request is instantiated without the send channel, then.

    .send_push_promise() is not available.
    """

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        # the server is push-enabled
        scope["extensions"]["http.response.push"] = {}  # type: ignore[index]

        data = "OK"
        request = Request[Any, Any, Any](scope)
        try:
            await request.send_push_promise("/style.css")
        except RuntimeError:
            data = "Send channel not available"
        response = ASGIResponse(body=encode_json({"json": data}))
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/")
    assert response.json() == {"json": "Send channel not available"}


class BeforeRequestMiddleWare(MiddlewareProtocol):
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["state"]["main"] = 1
        await self.app(scope, receive, send)


def test_state() -> None:
    def before_request(request: Request) -> None:
        assert request.state.main == 1
        request.state.main = 2

    @get(path="/", signature_namespace={"dict": Dict})
    async def get_state(request: Request) -> dict[str, str]:
        return {"state": request.state.main}

    with create_test_client(
        route_handlers=[get_state], middleware=[BeforeRequestMiddleWare], before_request=before_request
    ) as client:
        response = client.get("/")
        assert response.json() == {"state": 2}
