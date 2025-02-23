from typing import Callable

import pytest

from litestar.handlers import HTTPRouteHandler
from litestar.handlers.http_handlers import delete, get, patch, post, put, route
from litestar.types import AnyCallable


@pytest.mark.parametrize("handler_decorator", [get, put, delete, post, patch])
def test_custom_handler_class(handler_decorator: Callable[..., Callable[[AnyCallable], HTTPRouteHandler]]) -> None:
    class MyHandlerClass(HTTPRouteHandler):
        pass

    @handler_decorator("/", handler_class=MyHandlerClass)
    async def handler() -> None:
        pass

    assert isinstance(handler, MyHandlerClass)


def test_custom_handler_class_route() -> None:
    class MyHandlerClass(HTTPRouteHandler):
        pass

    @route("/", handler_class=MyHandlerClass, http_method="GET")
    async def handler() -> None:
        pass

    assert isinstance(handler, MyHandlerClass)
