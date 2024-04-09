from typing import Optional, Type

import pytest

from litestar import Controller, HttpMethod, Litestar, Response, Router, get
from litestar.handlers.http_handlers.base import HTTPRouteHandler

RouterResponse: Type[Response] = type("RouterResponse", (Response,), {})
ControllerResponse: Type[Response] = type("ControllerResponse", (Response,), {})
AppResponse: Type[Response] = type("AppResponse", (Response,), {})
HandlerResponse: Type[Response] = type("HandlerResponse", (Response,), {})


@pytest.mark.parametrize(
    "handler_response_class, controller_response_class, router_response_class, app_response_class, expected",
    (
        (HandlerResponse, ControllerResponse, RouterResponse, AppResponse, HandlerResponse),
        (None, ControllerResponse, RouterResponse, AppResponse, ControllerResponse),
        (None, None, RouterResponse, AppResponse, RouterResponse),
        (None, None, None, AppResponse, AppResponse),
        (None, None, None, None, Response),
    ),
    ids=(
        "Custom class for all layers",
        "Custom class for all above handler layer",
        "Custom class for all above controller layer",
        "Custom class for all above router layer",
        "No custom class for layers",
    ),
)
def test_response_class_resolution_of_layers(
    handler_response_class: Optional[Type[Response]],
    controller_response_class: Optional[Type[Response]],
    router_response_class: Optional[Type[Response]],
    app_response_class: Optional[Type[Response]],
    expected: Type[Response],
) -> None:
    class MyController(Controller):
        @get()
        def handler(self) -> None:
            pass

    if controller_response_class:
        MyController.response_class = ControllerResponse

    router = Router(path="/", route_handlers=[MyController])

    if router_response_class:
        router.response_class = router_response_class

    app = Litestar(route_handlers=[router])

    if app_response_class:
        app.response_class = app_response_class

    route_handler: HTTPRouteHandler = app.route_handler_method_map["/"][HttpMethod.GET]  # type: ignore[assignment]

    if handler_response_class:
        route_handler.response_class = handler_response_class

    response_class = route_handler.resolve_response_class()
    assert response_class is expected
