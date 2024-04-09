from typing import Any, Literal, Type, Union
from unittest import mock

import pytest

from litestar import Controller, Litestar, Router, get
from litestar.datastructures.url import URL
from litestar.enums import HttpMethod
from litestar.handlers.http_handlers.base import HTTPRouteHandler
from litestar.handlers.websocket_handlers.listener import (
    WebsocketListener,
    WebsocketListenerRouteHandler,
    websocket_listener,
)
from litestar.types.composite_types import TypeDecodersSequence

handler_decoder, router_decoder, controller_decoder, app_decoder = 4 * [(lambda t: t is URL, lambda t, v: URL(v))]


@pytest.fixture(scope="module")
def controller() -> Type[Controller]:
    class MyController(Controller):
        path = "/controller"
        type_decoders = [controller_decoder]

        @get("/http", type_decoders=[handler_decoder])
        def http(self) -> Any: ...

        @websocket_listener("/ws", type_decoders=[handler_decoder])
        async def handler(self, data: str) -> None: ...

    return MyController


@pytest.fixture(scope="module")
def websocket_listener_handler() -> Type[WebsocketListener]:
    class WebSocketHandler(WebsocketListener):
        path = "/ws-listener"
        type_decoders = [handler_decoder]

        def on_receive(self, data: str) -> None:  # pyright: ignore [reportIncompatibleMethodOverride]
            ...

    return WebSocketHandler


@pytest.fixture(scope="module")
def http_handler() -> HTTPRouteHandler:
    @get("/http", type_decoders=[handler_decoder])
    def http() -> Any: ...

    return http


@pytest.fixture(scope="module")
def websocket_handler() -> WebsocketListenerRouteHandler:
    @websocket_listener("/ws", type_decoders=[handler_decoder])
    async def websocket(data: str) -> None: ...

    return websocket


@pytest.fixture(scope="module")
def router(
    controller: Type[Controller],
    websocket_listener_handler: Type[WebsocketListenerRouteHandler],
    http_handler: Type[HTTPRouteHandler],
    websocket_handler: Type[WebsocketListenerRouteHandler],
) -> Router:
    return Router(
        "/router",
        type_decoders=[router_decoder],
        route_handlers=[controller, websocket_listener_handler, http_handler, websocket_handler],
    )


@pytest.fixture(scope="module")
@mock.patch("litestar.app.Litestar._get_default_plugins", mock.Mock(return_value=[]))
def app(router: Router) -> Litestar:
    return Litestar([router], type_decoders=[app_decoder])


@pytest.mark.parametrize(
    "path, method, type_decoders",
    (
        ("/router/controller/http", HttpMethod.GET, [app_decoder, router_decoder, controller_decoder, handler_decoder]),
        ("/router/controller/ws", "websocket", [app_decoder, router_decoder, controller_decoder, handler_decoder]),
        ("/router/http", HttpMethod.GET, [app_decoder, router_decoder, handler_decoder]),
        ("/router/ws", "websocket", [app_decoder, router_decoder, handler_decoder]),
        ("/router/ws-listener", "websocket", [app_decoder, router_decoder, handler_decoder]),
    ),
    ids=(
        "Controller http endpoint type decoders",
        "Controller ws endpoint type decoders",
        "Router http endpoint type decoders",
        "Router ws endpoint type decoders",
        "Router ws listener type decoders",
    ),
)
def test_resolve_type_decoders(
    path: str, method: Union[HttpMethod, Literal["websocket"]], type_decoders: TypeDecodersSequence, app: Litestar
) -> None:
    handler = app.route_handler_method_map[path][method]
    assert handler.resolve_type_decoders() == type_decoders
