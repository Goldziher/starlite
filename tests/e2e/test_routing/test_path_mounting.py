from pathlib import Path
from typing import TYPE_CHECKING, Callable

import httpx
import pytest
from _pytest.monkeypatch import MonkeyPatch

from litestar import Litestar, MediaType, asgi, get, websocket
from litestar.exceptions import ImproperlyConfiguredException
from litestar.response.base import ASGIResponse
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from litestar.connection import WebSocket
    from litestar.types import Receive, Scope, Send


def test_supports_mounting() -> None:
    @asgi("/base/sub/path", is_mount=True)
    async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = ASGIResponse(body=scope["path"].encode(), media_type=MediaType.TEXT)
        await response(scope, receive, send)

    @asgi("/sub/path", is_mount=True)
    async def asgi_handler_mount_path(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = ASGIResponse(body=scope["path"].encode(), media_type=MediaType.TEXT)
        await response(scope, receive, send)

    @asgi("/not/mount")
    async def asgi_handler_not_mounted_path(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = ASGIResponse(body=scope["path"].encode(), media_type=MediaType.TEXT)
        await response(scope, receive, send)

    with create_test_client(
        route_handlers=[asgi_handler, asgi_handler_mount_path, asgi_handler_not_mounted_path]
    ) as client:
        response = client.get("/base/sub/path")
        assert response.status_code == HTTP_200_OK
        assert response.text == "/"

        response = client.get("/base/sub/path/abcd")
        assert response.status_code == HTTP_200_OK
        assert response.text == "/abcd/"

        response = client.get("/base/sub/path/abcd/complex/123/terminus")
        assert response.status_code == HTTP_200_OK
        assert response.text == "/abcd/complex/123/terminus/"

        response = client.get("/sub/path/deep/path")
        assert response.status_code == HTTP_200_OK
        assert response.text == "/deep/path/"

        response = client.get("/not/mount")
        assert response.status_code == HTTP_200_OK
        assert response.text == "/not/mount"


def test_supports_sub_routes_below_asgi_handlers() -> None:
    @asgi("/base/sub/path")
    async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = ASGIResponse(body=scope["path"].encode(), media_type=MediaType.TEXT)
        await response(scope, receive, send)

    @get("/base/sub/path/abc")
    def regular_handler() -> None:
        return

    assert Litestar(route_handlers=[asgi_handler, regular_handler])


def test_does_not_support_asgi_handlers_on_same_level_as_regular_handlers() -> None:
    @asgi("/base/sub/path")
    async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = ASGIResponse(body=scope["path"].encode(), media_type=MediaType.TEXT)
        await response(scope, receive, send)

    @get("/base/sub/path")
    def regular_handler() -> None:
        return

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[asgi_handler, regular_handler])


def test_does_not_support_asgi_handlers_on_same_level_as_websockets() -> None:
    @asgi("/base/sub/path")
    async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = ASGIResponse(body=scope["path"].encode(), media_type=MediaType.TEXT)
        await response(scope, receive, send)

    @websocket("/base/sub/path")
    async def regular_handler(socket: "WebSocket") -> None:
        return

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[asgi_handler, regular_handler])


@pytest.mark.parametrize(
    "server_command",
    [
        pytest.param(["uvicorn", "app:app", "--port", "9999"], id="uvicorn"),
        pytest.param(["hypercorn", "app:app", "--bind", "127.0.0.1:9999"], id="hypercorn"),
        pytest.param(["daphne", "app:app", "--port", "9999"], id="daphne"),
    ],
)
@pytest.mark.xdist_group("live_server_test")
@pytest.mark.server_integration
def test_path_mounting_live_server(
    tmp_path: Path, monkeypatch: MonkeyPatch, server_command: list[str], run_server: Callable[[str, list[str]], None]
) -> None:
    app = """
from litestar import asgi, Litestar
from litestar.types import Receive, Scope, Send
from litestar.response.base import ASGIResponse

@asgi("/sub/path", is_mount=True)
async def handler(scope: Scope, receive: Receive, send: Send) -> None:
    response = ASGIResponse(body=scope["path"].encode())
    await response(scope, receive, send)


app = Litestar(route_handlers=[handler])
"""
    run_server(app, server_command)

    res = httpx.get("http://127.0.0.1:9999/sub/path/fragment")
    assert res.status_code == 200
    assert res.text == "/fragment/"
