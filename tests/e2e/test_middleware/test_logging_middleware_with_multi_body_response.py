import pytest

from litestar import asgi
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.testing import create_async_test_client
from litestar.types.asgi_types import Receive, Scope, Send

pytestmark = pytest.mark.anyio


@asgi("/")
async def asgi_app(scope: Scope, receive: Receive, send: Send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"text/event-stream"),
                (b"cache-control", b"no-cache"),
                (b"connection", b"keep-alive"),
            ],
        }
    )

    # send two bodies
    await send({"type": "http.response.body", "body": b"data: 1\n", "more_body": True})
    await send({"type": "http.response.body", "body": b"data: 2\n", "more_body": False})


@pytest.mark.anyio
async def test_app() -> None:
    async with create_async_test_client(asgi_app, middleware=[LoggingMiddlewareConfig().middleware]) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.text == "data: 1\ndata: 2\n"
