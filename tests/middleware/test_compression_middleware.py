from typing import Any, AsyncIterator, cast

import brotli
import pytest
from typing_extensions import Literal

from starlite import MediaType, WebSocket, get, websocket
from starlite.config import CompressionConfig
from starlite.datastructures import Stream
from starlite.middleware.compression.brotli import BrotliMiddleware, CompressionEncoding
from starlite.middleware.compression.gzip import GZipMiddleware
from starlite.testing import create_test_client

BrotliMode = Literal["text", "generic", "font"]


@get(path="/", media_type=MediaType.TEXT)
def handler() -> str:
    return "_starlite_" * 4000


@get(path="/no-compression", media_type=MediaType.TEXT)
def no_compress_handler() -> str:
    return "_starlite_"


async def streaming_iter(content: bytes, count: int) -> AsyncIterator[bytes]:
    for _ in range(count):
        yield content


def test_no_compression_backend() -> None:
    try:
        client = create_test_client(route_handlers=[handler])
        unpacked_middleware = []
        cur = client.app.asgi_handler
        while hasattr(cur, "app"):
            unpacked_middleware.append(cur)
            cur = cast("Any", cur.app)  # type: ignore
        else:
            unpacked_middleware.append(cur)
        for middleware in unpacked_middleware:
            assert not isinstance(middleware, (GZipMiddleware, BrotliMiddleware))
    except Exception as exc:
        assert isinstance(exc, ValueError)
        assert "No compression backend specified" in str(exc)


def test_gzip_middleware_from_enum() -> None:
    client = create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="gzip"))
    unpacked_middleware = []
    cur = client.app.asgi_handler
    while hasattr(cur, "app"):
        unpacked_middleware.append(cur)
        cur = cast("Any", cur.app)  # type: ignore
    else:
        unpacked_middleware.append(cur)
    assert len(unpacked_middleware) == 4
    gzip_middleware = unpacked_middleware[1].handler  # type: ignore
    assert isinstance(gzip_middleware, GZipMiddleware)
    assert gzip_middleware.minimum_size == 500
    assert gzip_middleware.compresslevel == 9


def test_gzip_middleware_custom_settings() -> None:
    client = create_test_client(
        route_handlers=[handler],
        compression_config=CompressionConfig(backend="gzip", minimum_size=1000, gzip_compress_level=3),
    )
    unpacked_middleware = []
    cur = cast("Any", client.app.asgi_handler)
    while hasattr(cur, "app"):
        unpacked_middleware.append(cur)
        cur = cast("Any", cur.app)
    else:
        unpacked_middleware.append(cur)
    assert len(unpacked_middleware) == 4
    middleware = cast("Any", unpacked_middleware[1])
    gzip_middleware = middleware.handler
    assert isinstance(gzip_middleware, GZipMiddleware)
    assert gzip_middleware.minimum_size == 1000
    assert gzip_middleware.compresslevel == 3


def test_gzip_middleware_set_from_string() -> None:
    client = create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="gzip"))
    unpacked_middleware = []
    cur = cast("Any", client.app.asgi_handler)
    while hasattr(cur, "app"):
        unpacked_middleware.append(cur)
        cur = cast("Any", cur.app)
    else:
        unpacked_middleware.append(cur)
    assert len(unpacked_middleware) == 4
    middleware = cast("Any", unpacked_middleware[1])
    gzip_middleware = middleware.handler
    assert isinstance(gzip_middleware, GZipMiddleware)
    assert gzip_middleware.minimum_size == 500
    assert gzip_middleware.compresslevel == 9


def test_brotli_middleware_from_string() -> None:
    client = create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="brotli"))
    unpacked_middleware = []
    cur = client.app.asgi_handler
    while hasattr(cur, "app"):
        unpacked_middleware.append(cur)
        cur = cast("Any", cur.app)  # type: ignore
    else:
        unpacked_middleware.append(cur)
    assert len(unpacked_middleware) == 4
    brotli_middleware = unpacked_middleware[1].handler  # type: ignore
    assert isinstance(brotli_middleware, BrotliMiddleware)
    assert brotli_middleware.quality == 5
    assert brotli_middleware.mode == BrotliMiddleware._brotli_mode_to_int("text")
    assert brotli_middleware.lgwin == 22
    assert brotli_middleware.lgblock == 0


def test_brotli_encoding_disable_for_unsupported_client() -> None:
    with create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="brotli")) as client:
        response = client.request("GET", "/", headers={"accept-encoding": "deflate"})
        assert response.status_code == 200, response.text
        assert response.text == "_starlite_" * 4000
        assert "Content-Encoding" not in response.headers
        assert int(response.headers["Content-Length"]) == 40000


def test_brotli_regular_response() -> None:
    with create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="brotli")) as client:
        response = client.request("GET", "/")
        assert response.status_code == 200, response.text
        assert response.text == "_starlite_" * 4000
        assert response.headers["Content-Encoding"] == CompressionEncoding.BROTLI
        assert int(response.headers["Content-Length"]) < 40000


async def test_brotli_streaming_response(anyio_backend: str) -> None:
    iterator = streaming_iter(content=b"_starlite_" * 400, count=10)

    @get("/streaming-response")
    def streaming_handler() -> Stream:
        return Stream(iterator=iterator)

    with create_test_client(
        route_handlers=[streaming_handler], compression_config=CompressionConfig(backend="brotli")
    ) as client:
        response = client.request("GET", "/streaming-response")
        assert response.status_code == 200, response.text
        assert response.text == "_starlite_" * 4000
        assert response.headers["Content-Encoding"] == CompressionEncoding.BROTLI
        assert "Content-Length" not in response.headers


def test_brotli_dont_compress_small_responses() -> None:
    with create_test_client(
        route_handlers=[no_compress_handler], compression_config=CompressionConfig(backend="brotli")
    ) as client:
        response = client.request("GET", "/no-compression")
        assert response.status_code == 200, response.text
        assert response.text == "_starlite_"
        assert "Content-Encoding" not in response.headers
        assert int(response.headers["Content-Length"]) == 10


def test_brotli_gzip_fallback_enabled() -> None:
    with create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="brotli")) as client:
        response = client.request("GET", "/", headers={"accept-encoding": "gzip"})
        assert response.status_code == 200, response.text
        assert response.text == "_starlite_" * 4000
        assert response.headers["Content-Encoding"] == CompressionEncoding.GZIP
        assert int(response.headers["Content-Length"]) < 40000


def test_brotli_gzip_fallback_disabled() -> None:
    with create_test_client(
        route_handlers=[handler],
        compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=False),
    ) as client:
        response = client.request("GET", "/", headers={"accept-encoding": "gzip"})
        assert response.status_code == 200, response.text
        assert response.text == "_starlite_" * 4000
        assert "Content-Encoding" not in response.headers
        assert int(response.headers["Content-Length"]) == 40000


def test_brotli_middleware_custom_settings() -> None:
    client = create_test_client(
        route_handlers=[handler],
        compression_config=CompressionConfig(
            backend="brotli",
            minimum_size=1000,
            brotli_quality=3,
            brotli_mode="font",
            brotli_lgwin=20,
            brotli_lgblock=17,
        ),
    )
    unpacked_middleware = []
    cur = client.app.asgi_handler
    while hasattr(cur, "app"):
        unpacked_middleware.append(cur)
        cur = cast("Any", cur.app)  # type: ignore
    else:
        unpacked_middleware.append(cur)
    assert len(unpacked_middleware) == 4
    brotli_middleware = unpacked_middleware[1].handler  # type: ignore
    assert isinstance(brotli_middleware, BrotliMiddleware)
    assert brotli_middleware.quality == 3
    assert brotli_middleware.mode == BrotliMiddleware._brotli_mode_to_int("font")
    assert brotli_middleware.lgwin == 20
    assert brotli_middleware.lgblock == 17


def test_brotli_middleware_invalid_mode() -> None:
    try:
        create_test_client(
            route_handlers=[handler],
            compression_config=CompressionConfig(
                backend="brotli",
                brotli_mode="BINARY",  # type: ignore
            ),
        )
    except Exception as exc:
        assert isinstance(exc, ValueError)
        assert "unexpected value" in str(exc)


def test_invalid_compression_middleware() -> None:
    try:
        create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="super-zip"))  # type: ignore
    except Exception as exc:
        assert isinstance(exc, ValueError)


@pytest.mark.parametrize(
    "mode, exp",
    [
        ("text", brotli.MODE_TEXT),
        ("font", brotli.MODE_FONT),
        ("generic", brotli.MODE_GENERIC),
    ],
)
def test_brotli_middleware_brotli_mode_to_int(mode: BrotliMode, exp: int) -> None:
    assert BrotliMiddleware._brotli_mode_to_int(mode) == exp


async def test_skips_for_websocket() -> None:
    @websocket("/")
    async def websocket_handler(socket: WebSocket) -> None:
        data = await socket.receive_json()
        await socket.send_json(data)
        await socket.close()

    with create_test_client(
        route_handlers=[websocket_handler],
        compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=False),
    ).websocket_connect("/") as ws:
        assert b"content-encoding" not in dict(ws.scope["headers"])
