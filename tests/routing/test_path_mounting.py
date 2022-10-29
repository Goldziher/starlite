from typing import TYPE_CHECKING

import pytest

from starlite import (
    ImproperlyConfiguredException,
    MediaType,
    Response,
    Starlite,
    asgi,
    get,
    websocket,
)
from starlite.status_codes import HTTP_200_OK
from starlite.testing import create_test_client

if TYPE_CHECKING:
    from starlite.connection import WebSocket
    from starlite.types import Receive, Scope, Send


def test_supports_mounting() -> None:
    @asgi("/base/sub/path", is_mount=True)
    async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = Response(scope["path"], media_type=MediaType.TEXT, status_code=HTTP_200_OK)
        await response(scope, receive, send)

    with create_test_client(asgi_handler) as client:
        response = client.get("/base/sub/path")
        assert response.status_code == HTTP_200_OK
        assert response.text == "/"

        response = client.get("/base/sub/path/abcd")
        assert response.status_code == HTTP_200_OK
        assert response.text == "/abcd"

        response = client.get("/base/sub/path/abcd/complex/123/terminus")
        assert response.status_code == HTTP_200_OK
        assert response.text == "/abcd/complex/123/terminus"


def test_supports_sub_routes_below_asgi_handlers() -> None:
    @asgi("/base/sub/path")
    async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = Response(scope["path"], media_type=MediaType.TEXT, status_code=HTTP_200_OK)
        await response(scope, receive, send)

    @get("/base/sub/path/abc")
    def regular_handler() -> None:
        return

    assert Starlite(route_handlers=[asgi_handler, regular_handler])


def test_does_not_support_asgi_handlers_on_same_level_as_regular_handlers() -> None:
    @asgi("/base/sub/path")
    async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = Response(scope["path"], media_type=MediaType.TEXT, status_code=HTTP_200_OK)
        await response(scope, receive, send)

    @get("/base/sub/path")
    def regular_handler() -> None:
        return

    with pytest.raises(ImproperlyConfiguredException):
        Starlite(route_handlers=[asgi_handler, regular_handler])


def test_does_not_support_asgi_handlers_on_same_level_as_websockets() -> None:
    @asgi("/base/sub/path")
    async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None:
        response = Response(scope["path"], media_type=MediaType.TEXT, status_code=HTTP_200_OK)
        await response(scope, receive, send)

    @websocket("/base/sub/path")
    async def regular_handler(socket: "WebSocket") -> None:
        return

    with pytest.raises(ImproperlyConfiguredException):
        Starlite(route_handlers=[asgi_handler, regular_handler])
