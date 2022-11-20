from typing import AsyncIterator, Literal

import pytest

from starlite import MediaType, WebSocket, get, websocket
from starlite.config import CompressionConfig
from starlite.datastructures import Stream
from starlite.enums import CompressionEncoding
from starlite.status_codes import HTTP_200_OK
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


def test_compression_disabled_for_unsupported_client() -> None:
    with create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="brotli")) as client:
        response = client.get("/", headers={"accept-encoding": "deflate"})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_starlite_" * 4000
        assert "Content-Encoding" not in response.headers
        assert int(response.headers["Content-Length"]) == 40000


@pytest.mark.parametrize(
    "backend, compression_encoding", (("brotli", CompressionEncoding.BROTLI), ("gzip", CompressionEncoding.GZIP))
)
def test_regular_compressed_response(
    backend: Literal["gzip", "brotli"], compression_encoding: CompressionEncoding
) -> None:
    with create_test_client(route_handlers=[handler], compression_config=CompressionConfig(backend="brotli")) as client:
        response = client.get("/", headers={"Accept-Encoding": str(compression_encoding.value)})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_starlite_" * 4000
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
        return Stream(iterator=streaming_iter(content=b"_starlite_" * 400, count=10))

    with create_test_client(
        route_handlers=[streaming_handler], compression_config=CompressionConfig(backend=backend)
    ) as client:
        response = client.get("/streaming-response", headers={"Accept-Encoding": str(compression_encoding.value)})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_starlite_" * 4000
        assert response.headers["Content-Encoding"] == compression_encoding
        assert "Content-Length" not in response.headers


@pytest.mark.parametrize(
    "backend, compression_encoding", (("brotli", CompressionEncoding.BROTLI), ("gzip", CompressionEncoding.GZIP))
)
def test_compression_skips_small_responses(
    backend: Literal["gzip", "brotli"], compression_encoding: CompressionEncoding
) -> None:
    with create_test_client(
        route_handlers=[no_compress_handler], compression_config=CompressionConfig(backend=backend)
    ) as client:
        response = client.get("/no-compression", headers={"Accept-Encoding": str(compression_encoding.value)})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_starlite_"
        assert "Content-Encoding" not in response.headers
        assert int(response.headers["Content-Length"]) == 10


def test_brotli_with_gzip_fallback_enabled() -> None:
    with create_test_client(
        route_handlers=[handler], compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=True)
    ) as client:
        response = client.get("/", headers={"accept-encoding": CompressionEncoding.GZIP.value})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_starlite_" * 4000
        assert response.headers["Content-Encoding"] == CompressionEncoding.GZIP
        assert int(response.headers["Content-Length"]) < 40000


def test_brotli_gzip_fallback_disabled() -> None:
    with create_test_client(
        route_handlers=[handler],
        compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=False),
    ) as client:
        response = client.get("/", headers={"accept-encoding": "gzip"})
        assert response.status_code == HTTP_200_OK
        assert response.text == "_starlite_" * 4000
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
