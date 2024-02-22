import zlib
from io import BytesIO
from typing import AsyncIterator, Callable, Literal, Union
from unittest.mock import MagicMock

import pytest

from litestar import MediaType, WebSocket, get, websocket
from litestar.config.compression import CompressionConfig
from litestar.enums import CompressionEncoding
from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers import HTTPRouteHandler
from litestar.middleware.compression import CompressionMiddleware
from litestar.middleware.compression.facade import CompressionFacade
from litestar.response.streaming import Stream
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client
from litestar.types.asgi_types import ASGIApp, HTTPResponseBodyEvent, HTTPResponseStartEvent, Message, Scope

BrotliMode = Literal["text", "generic", "font"]


@pytest.fixture()
def handler() -> HTTPRouteHandler:
    @get(path="/", media_type=MediaType.TEXT)
    def handler_fn() -> str:
        return "_litestar_" * 4000

    return handler_fn


async def streaming_iter(content: bytes, count: int) -> AsyncIterator[bytes]:
    for _ in range(count):
        yield content


def test_compression_disabled_for_unsupported_client(handler: HTTPRouteHandler) -> None:
    with create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="brotli")) as client:
        response = client.get("/", headers={"accept-encoding": "deflate"})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_litestar_" * 4000
        assert "Content-Encoding" not in response.headers
        assert int(response.headers["Content-Length"]) == 40000


@pytest.mark.parametrize(
    "backend, compression_encoding", (("brotli", CompressionEncoding.BROTLI), ("gzip", CompressionEncoding.GZIP))
)
def test_regular_compressed_response(
    backend: Literal["gzip", "brotli"], compression_encoding: CompressionEncoding, handler: HTTPRouteHandler
) -> None:
    with create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="brotli")) as client:
        response = client.get("/", headers={"Accept-Encoding": str(compression_encoding.value)})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_litestar_" * 4000
        assert response.headers["Content-Encoding"] == compression_encoding
        assert int(response.headers["Content-Length"]) < 40000


@pytest.mark.parametrize(
    "backend, compression_encoding", (("brotli", CompressionEncoding.BROTLI), ("gzip", CompressionEncoding.GZIP))
)
def test_compression_works_for_streaming_response(
    backend: Literal["gzip", "brotli"], compression_encoding: CompressionEncoding
) -> None:
    @get("/streaming-response")
    def streaming_handler() -> Stream:
        return Stream(streaming_iter(content=b"_litestar_" * 400, count=10))

    with create_test_client(
        route_handlers=[streaming_handler], compression_config=CompressionConfig(backend=backend)
    ) as client:
        response = client.get("/streaming-response", headers={"Accept-Encoding": str(compression_encoding.value)})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_litestar_" * 4000
        assert response.headers["Content-Encoding"] == compression_encoding
        assert "Content-Length" not in response.headers


@pytest.mark.parametrize(
    "backend, compression_encoding", (("brotli", CompressionEncoding.BROTLI), ("gzip", CompressionEncoding.GZIP))
)
def test_compression_skips_small_responses(
    backend: Literal["gzip", "brotli"], compression_encoding: CompressionEncoding
) -> None:
    @get(path="/no-compression", media_type=MediaType.TEXT)
    def no_compress_handler() -> str:
        return "_litestar_"

    with create_test_client(
        route_handlers=[no_compress_handler], compression_config=CompressionConfig(backend=backend)
    ) as client:
        response = client.get("/no-compression", headers={"Accept-Encoding": str(compression_encoding.value)})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_litestar_"
        assert "Content-Encoding" not in response.headers
        assert int(response.headers["Content-Length"]) == 10


def test_brotli_with_gzip_fallback_enabled(handler: HTTPRouteHandler) -> None:
    with create_test_client(
        route_handlers=[handler], compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=True)
    ) as client:
        response = client.get("/", headers={"accept-encoding": CompressionEncoding.GZIP.value})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_litestar_" * 4000
        assert response.headers["Content-Encoding"] == CompressionEncoding.GZIP
        assert int(response.headers["Content-Length"]) < 40000


def test_brotli_gzip_fallback_disabled(handler: HTTPRouteHandler) -> None:
    with create_test_client(
        route_handlers=[handler],
        compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=False),
    ) as client:
        response = client.get("/", headers={"accept-encoding": "gzip"})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_litestar_" * 4000
        assert "Content-Encoding" not in response.headers
        assert int(response.headers["Content-Length"]) == 40000


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


@pytest.mark.parametrize("minimum_size, should_raise", ((0, True), (1, False), (-1, True), (100, False)))
def test_config_minimum_size_validation(minimum_size: int, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            CompressionConfig(backend="brotli", brotli_gzip_fallback=False, minimum_size=minimum_size)
    else:
        CompressionConfig(backend="brotli", brotli_gzip_fallback=False, minimum_size=minimum_size)


@pytest.mark.parametrize(
    "gzip_compress_level, should_raise", ((0, False), (1, False), (-1, True), (10, True), (9, False))
)
def test_config_gzip_compress_level_validation(gzip_compress_level: int, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            CompressionConfig(backend="gzip", brotli_gzip_fallback=False, gzip_compress_level=gzip_compress_level)
    else:
        CompressionConfig(backend="gzip", brotli_gzip_fallback=False, gzip_compress_level=gzip_compress_level)


@pytest.mark.parametrize("brotli_quality, should_raise", ((0, False), (1, False), (-1, True), (12, True), (11, False)))
def test_config_brotli_quality_validation(brotli_quality: int, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            CompressionConfig(backend="brotli", brotli_gzip_fallback=False, brotli_quality=brotli_quality)
    else:
        CompressionConfig(backend="brotli", brotli_gzip_fallback=False, brotli_quality=brotli_quality)


@pytest.mark.parametrize("brotli_lgwin, should_raise", ((9, True), (10, False), (-1, True), (25, True), (24, False)))
def test_config_brotli_lgwin_validation(brotli_lgwin: int, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            CompressionConfig(backend="brotli", brotli_gzip_fallback=False, brotli_lgwin=brotli_lgwin)
    else:
        CompressionConfig(backend="brotli", brotli_gzip_fallback=False, brotli_lgwin=brotli_lgwin)


@pytest.mark.parametrize(
    "backend, compression_encoding", (("brotli", CompressionEncoding.BROTLI), ("gzip", CompressionEncoding.GZIP))
)
async def test_compression_streaming_response_emitted_messages(
    backend: Literal["gzip", "brotli"],
    compression_encoding: Literal[CompressionEncoding.BROTLI, CompressionEncoding.GZIP],
    create_scope: Callable[..., Scope],
    mock_asgi_app: ASGIApp,
) -> None:
    mock = MagicMock()

    async def fake_send(message: Message) -> None:
        mock(message)

    wrapped_send = CompressionMiddleware(
        mock_asgi_app, CompressionConfig(backend=backend)
    ).create_compression_send_wrapper(fake_send, compression_encoding, create_scope())

    await wrapped_send(HTTPResponseStartEvent(type="http.response.start", status=200, headers={}))
    # first body message always has compression headers (at least for gzip)
    await wrapped_send(HTTPResponseBodyEvent(type="http.response.body", body=b"abc", more_body=True))
    # second body message with more_body=True will be empty if zlib buffers output and is not flushed
    await wrapped_send(HTTPResponseBodyEvent(type="http.response.body", body=b"abc", more_body=True))
    assert mock.mock_calls[-1].args[0]["body"]


@pytest.mark.parametrize(
    "backend, compression_encoding", (("brotli", CompressionEncoding.BROTLI), ("gzip", CompressionEncoding.GZIP))
)
def test_dont_recompress_cached(backend: Literal["gzip", "brotli"], compression_encoding: CompressionEncoding) -> None:
    mock = MagicMock(return_value="_litestar_" * 4000)

    @get(path="/", media_type=MediaType.TEXT, cache=True)
    def handler_fn() -> str:
        return mock()  # type: ignore[no-any-return]

    with create_test_client(
        route_handlers=[handler_fn], compression_config=CompressionConfig(backend=backend)
    ) as client:
        client.get("/", headers={"Accept-Encoding": str(compression_encoding.value)})
        response = client.get("/", headers={"Accept-Encoding": str(compression_encoding.value)})

    assert mock.call_count == 1
    assert response.status_code == HTTP_200_OK
    assert response.text == "_litestar_" * 4000
    assert response.headers["Content-Encoding"] == compression_encoding
    assert int(response.headers["Content-Length"]) < 40000


def test_compression_with_custom_backend(handler: HTTPRouteHandler) -> None:
    class ZlibCompression(CompressionFacade):
        encoding = "deflate"

        def __init__(
            self,
            buffer: BytesIO,
            compression_encoding: Union[Literal[CompressionEncoding.GZIP], str],
            config: CompressionConfig,
        ) -> None:
            self.buffer = buffer
            self.compression_encoding = compression_encoding
            self.config = config

        def write(self, body: bytes) -> None:
            self.buffer.write(zlib.compress(body, level=self.config.backend_config["level"]))

        def close(self) -> None:
            ...

    zlib_config = {"level": 9}
    config = CompressionConfig(backend="deflate", compression_facade=ZlibCompression, backend_config=zlib_config)
    with create_test_client([handler], compression_config=config) as client:
        response = client.get("/", headers={"Accept-Encoding": "deflate"})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_litestar_" * 4000
        assert response.headers["Content-Encoding"] == "deflate"
        assert int(response.headers["Content-Length"]) < 40000
