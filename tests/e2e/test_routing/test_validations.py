from typing import Any

import pytest

from litestar import Controller, Litestar, WebSocket, get, websocket
from litestar.exceptions import ImproperlyConfiguredException
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


def test_register_validation_duplicate_handlers_for_same_route_and_method() -> None:
    @get(path="/first")
    def first_route_handler() -> None:
        pass

    @get(path="/first")
    def second_route_handler() -> None:
        pass

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[first_route_handler, second_route_handler])


def test_supports_websocket_and_http_handlers() -> None:
    @get(path="/")
    def http_handler() -> dict:
        return {"hello": "world"}

    @websocket(path="/")
    async def websocket_handler(socket: "WebSocket[Any, Any, Any]") -> None:
        await socket.accept()
        await socket.send_json({"hello": "world"})
        await socket.close()

    with create_test_client([http_handler, websocket_handler]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"hello": "world"}

        with client.websocket_connect("/") as ws:
            ws_response = ws.receive_json()
            assert ws_response == {"hello": "world"}


def test_controller_supports_websocket_and_http_handlers() -> None:
    class MyController(Controller):
        path = "/"

        @get()
        def http_handler(
            self,
        ) -> dict:
            return {"hello": "world"}

        @websocket()
        async def websocket_handler(self, socket: "WebSocket[Any, Any, Any]") -> None:
            await socket.accept()
            await socket.send_json({"hello": "world"})
            await socket.close()

    with create_test_client(MyController) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"hello": "world"}

        with client.websocket_connect("/") as ws:
            ws_response = ws.receive_json()
            assert ws_response == {"hello": "world"}
