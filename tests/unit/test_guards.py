from typing import TYPE_CHECKING

import pytest

from litestar import Litestar, Router, asgi, get, websocket
from litestar.connection import WebSocket
from litestar.exceptions import PermissionDeniedException, WebSocketDisconnect
from litestar.response.base import ASGIResponse
from litestar.status_codes import HTTP_200_OK, HTTP_403_FORBIDDEN
from litestar.testing import create_test_client
from litestar.types import Receive, Scope, Send

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler


async def local_guard(_: "ASGIConnection", route_handler: "BaseRouteHandler") -> None:
    if not route_handler.opt or not route_handler.opt.get("allow_all"):
        raise PermissionDeniedException("local")


def router_guard(connection: "ASGIConnection", _: "BaseRouteHandler") -> None:
    if not connection.headers.get("Authorization-Router"):
        raise PermissionDeniedException("router")


def app_guard(connection: "ASGIConnection", _: "BaseRouteHandler") -> None:
    if not connection.headers.get("Authorization"):
        raise PermissionDeniedException("app")


def test_guards_with_http_handler() -> None:
    @get(path="/secret", guards=[local_guard])
    def my_http_route_handler() -> None: ...

    with create_test_client(guards=[app_guard], route_handlers=[my_http_route_handler]) as client:
        response = client.get("/secret")
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "app"
        response = client.get("/secret", headers={"Authorization": "yes"})
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "local"
        client.app.asgi_router.root_route_map_node.children["/secret"].asgi_handlers["GET"][1].opt["allow_all"] = True
        response = client.get("/secret", headers={"Authorization": "yes"})
        assert response.status_code == HTTP_200_OK


def test_guards_with_asgi_handler() -> None:
    @asgi(path="/secret", guards=[local_guard])
    async def my_asgi_handler(scope: Scope, receive: Receive, send: Send) -> None:
        response = ASGIResponse(body=b'{"hello": "world"}')
        await response(scope=scope, receive=receive, send=send)

    with create_test_client(guards=[app_guard], route_handlers=[my_asgi_handler]) as client:
        response = client.get("/secret")
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "app"
        response = client.get("/secret", headers={"Authorization": "yes"})
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "local"
        client.app.asgi_router.root_route_map_node.children["/secret"].asgi_handlers["asgi"][1].opt["allow_all"] = True
        response = client.get("/secret", headers={"Authorization": "yes"})
        assert response.status_code == HTTP_200_OK


def test_guards_with_websocket_handler() -> None:
    @websocket(path="/", guards=[local_guard])
    async def my_websocket_route_handler(socket: WebSocket) -> None:
        await socket.accept()
        data = await socket.receive_json()
        assert data
        await socket.send_json({"data": "123"})
        await socket.close()

    client = create_test_client(route_handlers=my_websocket_route_handler)

    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/") as ws:
        ws.send_json({"data": "123"})

    client.app.asgi_router.root_route_map_node.children["/"].asgi_handlers["websocket"][1].opt["allow_all"] = True

    with client.websocket_connect("/") as ws:
        ws.send_json({"data": "123"})


def test_guards_layering_for_same_route_handler() -> None:
    @get(path="/http", guards=[local_guard])
    def http_route_handler() -> None: ...

    router = Router(path="/router", route_handlers=[http_route_handler], guards=[router_guard])
    app = Litestar(route_handlers=[http_route_handler, router], guards=[app_guard])

    assert (
        len(
            app.asgi_router.root_route_map_node.children["/http"]
            .asgi_handlers["GET"][1]  # type: ignore[arg-type]
            ._resolved_guards
        )
        == 2
    )
    assert (
        len(
            app.asgi_router.root_route_map_node.children["/router/http"]
            .asgi_handlers["GET"][1]  # type: ignore[arg-type]
            ._resolved_guards
        )
        == 3
    )
