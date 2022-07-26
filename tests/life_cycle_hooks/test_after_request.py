from typing import Optional

import pytest

from starlite import Controller, HTTPRouteHandler, Response, Router, get
from starlite.testing import create_test_client
from starlite.types import AfterRequestHandler


def greet() -> dict:
    return {"hello": "world"}


def sync_after_request_handler(response: Response) -> Response:
    assert isinstance(response, Response)
    response.body = response.render({"hello": "moon"})
    return response


async def async_after_request_handler(response: Response) -> Response:
    assert isinstance(response, Response)
    response.body = response.render({"hello": "moon"})
    return response


async def async_after_request_handler_with_hello_world(response: Response) -> Response:
    assert isinstance(response, Response)
    response.body = response.render({"hello": "world"})
    return response


@pytest.mark.parametrize(
    "handler, expected",
    [
        [get(path="/")(greet), {"hello": "world"}],
        [get(path="/", after_request=sync_after_request_handler)(greet), {"hello": "moon"}],
        [get(path="/", after_request=async_after_request_handler)(greet), {"hello": "moon"}],
    ],
)
def test_after_request_handler_called(handler: HTTPRouteHandler, expected: dict) -> None:
    with create_test_client(route_handlers=handler) as client:
        response = client.get("/")
        assert response.json() == expected


@pytest.mark.parametrize(
    "app_after_request_handler, router_after_request_handler, controller_after_request_handler, method_after_request_handler, expected",
    [
        [None, None, None, None, {"hello": "world"}],
        [sync_after_request_handler, None, None, None, {"hello": "moon"}],
        [None, sync_after_request_handler, None, None, {"hello": "moon"}],
        [None, None, sync_after_request_handler, None, {"hello": "moon"}],
        [None, None, None, sync_after_request_handler, {"hello": "moon"}],
        [sync_after_request_handler, async_after_request_handler_with_hello_world, None, None, {"hello": "world"}],
        [None, sync_after_request_handler, async_after_request_handler_with_hello_world, None, {"hello": "world"}],
        [None, None, sync_after_request_handler, async_after_request_handler_with_hello_world, {"hello": "world"}],
        [None, None, None, async_after_request_handler_with_hello_world, {"hello": "world"}],
    ],
)
def test_after_request_handler_resolution(
    app_after_request_handler: Optional[AfterRequestHandler],
    router_after_request_handler: Optional[AfterRequestHandler],
    controller_after_request_handler: Optional[AfterRequestHandler],
    method_after_request_handler: Optional[AfterRequestHandler],
    expected: dict,
) -> None:
    class MyController(Controller):
        path = "/hello"

        after_request = controller_after_request_handler

        @get(after_request=method_after_request_handler)
        def hello(self) -> dict:
            return {"hello": "world"}

    router = Router(path="/greetings", route_handlers=[MyController], after_request=router_after_request_handler)

    with create_test_client(route_handlers=router, after_request=app_after_request_handler) as client:
        response = client.get("/greetings/hello")
        assert response.json() == expected
