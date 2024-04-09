from typing import Any

import pytest

from litestar import Litestar, WebSocket, websocket
from litestar.exceptions import ImproperlyConfiguredException
from litestar.testing import create_test_client


def test_raises_when_socket_arg_is_missing() -> None:
    def fn_without_socket_arg(websocket: WebSocket) -> None:
        pass

    with pytest.raises(ImproperlyConfiguredException):
        websocket(path="/")(fn_without_socket_arg).on_registration(Litestar())  # type: ignore[arg-type]


def test_raises_for_return_annotation() -> None:
    async def fn_with_return_annotation(socket: WebSocket) -> dict:
        return {}

    with pytest.raises(ImproperlyConfiguredException):
        websocket(path="/")(fn_with_return_annotation).on_registration(Litestar())


def test_raises_when_no_function() -> None:
    websocket_handler_with_no_fn = websocket(path="/")

    with pytest.raises(ImproperlyConfiguredException):
        create_test_client(route_handlers=websocket_handler_with_no_fn)


def test_raises_when_sync_handler_user() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @websocket(path="/")  # type: ignore[arg-type]
        def sync_websocket_handler(socket: WebSocket) -> None: ...

        sync_websocket_handler.on_registration(Litestar())


def test_raises_when_data_kwarg_is_used() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @websocket(path="/")
        async def websocket_handler_with_data_kwarg(socket: WebSocket, data: Any) -> None: ...

        websocket_handler_with_data_kwarg.on_registration(Litestar())


def test_raises_when_request_kwarg_is_used() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @websocket(path="/")
        async def websocket_handler_with_request_kwarg(socket: WebSocket, request: Any) -> None: ...

        websocket_handler_with_request_kwarg.on_registration(Litestar())


def test_raises_when_body_kwarg_is_used() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @websocket(path="/")
        async def websocket_handler_with_request_kwarg(socket: WebSocket, body: bytes) -> None: ...

        websocket_handler_with_request_kwarg.on_registration(Litestar())
