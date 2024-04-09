from typing import Type, Union

import pytest

from litestar import Controller, Litestar, Router, WebSocket
from litestar.handlers.websocket_handlers.listener import WebsocketListener, websocket_listener

RouterWebSocket: Type[WebSocket] = type("RouterWebSocket", (WebSocket,), {})
ControllerWebSocket: Type[WebSocket] = type("ControllerWebSocket", (WebSocket,), {})
AppWebSocket: Type[WebSocket] = type("AppWebSocket", (WebSocket,), {})
HandlerWebSocket: Type[WebSocket] = type("HandlerWebSocket", (WebSocket,), {})


@pytest.mark.parametrize(
    "handler_websocket_class, controller_websocket_class, router_websocket_class, app_websocket_class, has_default_app_class, expected",
    (
        (HandlerWebSocket, ControllerWebSocket, RouterWebSocket, AppWebSocket, True, HandlerWebSocket),
        (None, ControllerWebSocket, RouterWebSocket, AppWebSocket, True, ControllerWebSocket),
        (None, None, RouterWebSocket, AppWebSocket, True, RouterWebSocket),
        (None, None, None, AppWebSocket, True, AppWebSocket),
        (None, None, None, None, True, WebSocket),
        (None, None, None, None, False, WebSocket),
    ),
    ids=(
        "Custom class for all layers",
        "Custom class for all above handler layer",
        "Custom class for all above controller layer",
        "Custom class for all above router layer",
        "No custom class for layers",
        "No default class in app",
    ),
)
def test_websocket_class_resolution_of_layers(
    handler_websocket_class: Union[Type[WebSocket], None],
    controller_websocket_class: Union[Type[WebSocket], None],
    router_websocket_class: Union[Type[WebSocket], None],
    app_websocket_class: Union[Type[WebSocket], None],
    has_default_app_class: bool,
    expected: Type[WebSocket],
) -> None:
    class MyController(Controller):
        @websocket_listener("/")
        def handler(self, data: str) -> None:
            return

    if controller_websocket_class:
        MyController.websocket_class = ControllerWebSocket

    router = Router(path="/", route_handlers=[MyController])

    if router_websocket_class:
        router.websocket_class = router_websocket_class

    app = Litestar(route_handlers=[router])

    if app_websocket_class or not has_default_app_class:
        app.websocket_class = app_websocket_class  # type: ignore[assignment]

    route_handler = app.routes[0].route_handler  # type: ignore[union-attr]

    if handler_websocket_class:
        route_handler.websocket_class = handler_websocket_class  # type: ignore[union-attr]

    websocket_class = route_handler.resolve_websocket_class()  # type: ignore[union-attr]
    assert websocket_class is expected


@pytest.mark.parametrize(
    "handler_websocket_class, router_websocket_class, app_websocket_class, has_default_app_class, expected",
    (
        (HandlerWebSocket, RouterWebSocket, AppWebSocket, True, HandlerWebSocket),
        (None, RouterWebSocket, AppWebSocket, True, RouterWebSocket),
        (None, None, AppWebSocket, True, AppWebSocket),
        (None, None, None, True, WebSocket),
        (None, None, None, False, WebSocket),
    ),
    ids=(
        "Custom class for all layers",
        "Custom class for all above handler layer",
        "Custom class for all above router layer",
        "No custom class for layers",
        "No default class in app",
    ),
)
def test_listener_websocket_class_resolution_of_layers(
    handler_websocket_class: Union[Type[WebSocket], None],
    router_websocket_class: Union[Type[WebSocket], None],
    app_websocket_class: Union[Type[WebSocket], None],
    has_default_app_class: bool,
    expected: Type[WebSocket],
) -> None:
    class Handler(WebsocketListener):
        path = "/"
        websocket_class = handler_websocket_class

        def on_receive(self, data: str) -> str:  # pyright: ignore
            return data

    router = Router(path="/", route_handlers=[Handler])

    if router_websocket_class:
        router.websocket_class = router_websocket_class

    app = Litestar(route_handlers=[router])

    if app_websocket_class or not has_default_app_class:
        app.websocket_class = app_websocket_class  # type: ignore[assignment]

    route_handler = app.routes[0].route_handler  # type: ignore[union-attr]

    if handler_websocket_class:
        route_handler.websocket_class = handler_websocket_class  # type: ignore[union-attr]

    websocket_class = route_handler.resolve_websocket_class()  # type: ignore[union-attr]
    assert websocket_class is expected
