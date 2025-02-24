import logging
from typing import Any, Dict, Optional, Union

import pytest

from litestar import Controller, Request, Response, Router, get
from litestar.datastructures import State
from litestar.testing import create_test_client
from litestar.types import AnyCallable, BeforeRequestHookHandler

logger = logging.getLogger(__name__)


async def async_before_request_handler_with_parent(
    request: Request[Any, Any, State], /, *, parent: Optional[BeforeRequestHookHandler] = None
) -> Optional[Dict[str, Union[str, int]]]:
    assert isinstance(request, Request)
    retval: Dict[str, Union[str, int]] = (None if parent is None else await parent(request)) or {}
    retval.setdefault("amended_count", 0)
    retval["amended_count"] += 1  # type: ignore[operator]
    return retval


def sync_before_request_handler_with_return_value(request: Request[Any, Any, State]) -> Dict[str, str]:
    assert isinstance(request, Request)
    return {"hello": "moon"}


async def async_before_request_handler_with_return_value(request: Request[Any, Any, State]) -> Dict[str, str]:
    assert isinstance(request, Request)
    return {"hello": "moon"}


def sync_before_request_handler_without_return_value(request: Request[Any, Any, State]) -> None:
    assert isinstance(request, Request)


async def async_before_request_handler_without_return_value(request: Request[Any, Any, State]) -> None:
    assert isinstance(request, Request)


def sync_after_request_handler(response: Response[Dict[str, str]]) -> Response[Dict[str, str]]:
    assert isinstance(response, Response)
    response.content = {"hello": "moon"}
    return response


async def async_after_request_handler(response: Response[Dict[str, str]]) -> Response[Dict[str, str]]:
    assert isinstance(response, Response)
    response.content = {"hello": "moon"}
    return response


@pytest.mark.parametrize(
    "before_request, expected",
    (
        (None, {"hello": "world"}),
        (sync_before_request_handler_with_return_value, {"hello": "moon"}),
        (async_before_request_handler_with_return_value, {"hello": "moon"}),
        (sync_before_request_handler_without_return_value, {"hello": "world"}),
        (async_before_request_handler_without_return_value, {"hello": "world"}),
    ),
)
def test_before_request_handler_called(before_request: Optional[AnyCallable], expected: Dict[str, str]) -> None:
    @get(before_request=before_request)
    def handler() -> Dict[str, str]:
        return {"hello": "world"}

    with create_test_client(route_handlers=handler) as client:
        response = client.get("/")
        assert response.json() == expected


@pytest.mark.parametrize(
    "app_before_request_handler, router_before_request_handler, controller_before_request_handler, method_before_request_handler, expected",
    [
        [None, None, None, None, {"hello": "world"}],
        [sync_before_request_handler_with_return_value, None, None, None, {"hello": "moon"}],
        [None, sync_before_request_handler_with_return_value, None, None, {"hello": "moon"}],
        [None, None, sync_before_request_handler_with_return_value, None, {"hello": "moon"}],
        [None, None, None, sync_before_request_handler_with_return_value, {"hello": "moon"}],
        [
            sync_before_request_handler_with_return_value,
            async_before_request_handler_without_return_value,
            None,
            None,
            {"hello": "world"},
        ],
        [
            None,
            sync_before_request_handler_with_return_value,
            async_before_request_handler_without_return_value,
            None,
            {"hello": "world"},
        ],
        [
            None,
            None,
            sync_before_request_handler_with_return_value,
            async_before_request_handler_without_return_value,
            {"hello": "world"},
        ],
        [None, None, None, async_before_request_handler_without_return_value, {"hello": "world"}],
        [
            sync_before_request_handler_with_return_value,
            None,
            None,
            async_before_request_handler_with_parent,
            {"hello": "moon", "amended_count": 1},
        ],
        [
            sync_before_request_handler_with_return_value,
            None,
            async_before_request_handler_with_parent,
            async_before_request_handler_with_parent,
            {"hello": "moon", "amended_count": 2},
        ],
        [
            sync_before_request_handler_with_return_value,
            async_before_request_handler_with_parent,
            async_before_request_handler_with_parent,
            async_before_request_handler_with_parent,
            {"hello": "moon", "amended_count": 3},
        ],
    ],
)
def test_before_request_handler_resolution(
    app_before_request_handler: Optional[BeforeRequestHookHandler],
    router_before_request_handler: Optional[BeforeRequestHookHandler],
    controller_before_request_handler: Optional[BeforeRequestHookHandler],
    method_before_request_handler: Optional[BeforeRequestHookHandler],
    expected: Dict[str, str],
) -> None:
    class MyController(Controller):
        path = "/hello"

        before_request = controller_before_request_handler

        @get(before_request=method_before_request_handler)
        def hello(self) -> Dict[str, str]:
            return {"hello": "world"}

    router = Router(path="/greetings", route_handlers=[MyController], before_request=router_before_request_handler)

    with create_test_client(route_handlers=router, before_request=app_before_request_handler) as client:
        response = client.get("/greetings/hello")
        assert response.json() == expected
