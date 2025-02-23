from typing import Optional

import pytest

from litestar import Controller, HttpMethod, Litestar, Response, Router, get
from litestar.handlers.http_handlers.base import HTTPRouteHandler

RouterResponse: type[Response] = type("RouterResponse", (Response,), {})
ControllerResponse: type[Response] = type("ControllerResponse", (Response,), {})
AppResponse: type[Response] = type("AppResponse", (Response,), {})
HandlerResponse: type[Response] = type("HandlerResponse", (Response,), {})


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
    handler_response_class: Optional[type[Response]],
    controller_response_class: Optional[type[Response]],
    router_response_class: Optional[type[Response]],
    app_response_class: Optional[type[Response]],
    expected: type[Response],
) -> None:
    class MyController(Controller):
        response_class = controller_response_class

        @get(response_class=handler_response_class)
        def handler(self) -> None:
            pass

    router = Router(path="/", route_handlers=[MyController], response_class=router_response_class)

    app = Litestar(route_handlers=[router], response_class=app_response_class)

    route_handler: HTTPRouteHandler = app.route_handler_method_map["/"][HttpMethod.GET]  # type: ignore[assignment]

    response_class = route_handler.response_class
    assert response_class is expected
