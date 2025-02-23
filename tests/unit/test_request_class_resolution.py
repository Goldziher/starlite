from typing import Optional

import pytest

from litestar import Controller, HttpMethod, Litestar, Request, Router, get
from litestar.handlers.http_handlers.base import HTTPRouteHandler

RouterRequest: type[Request] = type("RouterRequest", (Request,), {})
ControllerRequest: type[Request] = type("ControllerRequest", (Request,), {})
AppRequest: type[Request] = type("AppRequest", (Request,), {})
HandlerRequest: type[Request] = type("HandlerRequest", (Request,), {})


@pytest.mark.parametrize(
    "handler_request_class, controller_request_class, router_request_class, app_request_class, expected",
    (
        (HandlerRequest, ControllerRequest, RouterRequest, AppRequest, HandlerRequest),
        (None, ControllerRequest, RouterRequest, AppRequest, ControllerRequest),
        (None, None, RouterRequest, AppRequest, RouterRequest),
        (None, None, None, AppRequest, AppRequest),
        (None, None, None, None, Request),
        (None, None, None, None, Request),
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
def test_request_class_resolution_of_layers(
    handler_request_class: Optional[type[Request]],
    controller_request_class: Optional[type[Request]],
    router_request_class: Optional[type[Request]],
    app_request_class: Optional[type[Request]],
    expected: type[Request],
) -> None:
    class MyController(Controller):
        request_class = controller_request_class

        @get(request_class=handler_request_class)
        def handler(self, request: Request) -> None:
            assert type(request) is expected

    router = Router(path="/", route_handlers=[MyController], request_class=router_request_class)

    app = Litestar(route_handlers=[router], request_class=app_request_class)

    route_handler: HTTPRouteHandler = app.route_handler_method_map["/"][HttpMethod.GET]  # type: ignore[assignment]

    request_class = route_handler.request_class
    assert request_class is expected
