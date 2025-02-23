from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest

from litestar import Litestar, get
from litestar._asgi.routing_trie.mapping import build_route_middleware_stack
from litestar.middleware._internal.exceptions import ExceptionHandlerMiddleware
from litestar.routes import HTTPRoute


def test_build_route_middleware_stack_no_middleware(monkeypatch: pytest.MonkeyPatch) -> None:
    # if there is no middleware for the route, then we don't need to wrap route.handle in
    # exception handling middleware. Exceptions can safely be caught by the outermost exception
    # handling middleware.

    @get("/")
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler], openapi_config=None)
    route = app.routes[0]
    handle_mock = MagicMock()
    monkeypatch.setattr(type(route), "handle", handle_mock)
    asgi_app = build_route_middleware_stack(app=app, route=route, route_handler=handler)
    assert asgi_app is handle_mock


def test_build_route_middleware_stack_with_middleware(monkeypatch: pytest.MonkeyPatch) -> None:
    # proves that if there is middleware, the route handler is wrapped in the exception handling
    # middleware, before being wrapped in the middleware stack.
    mock_middleware = MagicMock()
    del mock_middleware.__iter__

    @get("/", middleware=[mock_middleware])
    async def handler() -> None:
        pass

    route = HTTPRoute(path="/", route_handlers=[handler])
    build_route_middleware_stack(app=Litestar(), route=route, route_handler=handler)
    mock_middleware.assert_called_once()
    ((_, kw_args),) = mock_middleware.call_args_list
    assert isinstance(kw_args["app"], ExceptionHandlerMiddleware)


def test_build_route_middleware_stack_with_starlette_middleware(monkeypatch: pytest.MonkeyPatch) -> None:
    # test our support for starlette's Middleware class
    class Middleware:
        """A Starlette ``Middleware`` class.

        See https://github.com/encode/starlette/blob/23c81da94b57701eabd43f582093442e6811f81d/starlette/middleware/__init__.py#L4-L17
        """

        def __init__(self, cls: Any, **options: Any) -> None:
            self.cls = cls
            self.options = options

        def __iter__(self) -> Iterator[Any]:
            as_tuple = (self.cls, self.options)
            return iter(as_tuple)

    mock_middleware = MagicMock()
    mock_middleware_arg = MagicMock()
    del mock_middleware.__iter__

    @get("/", middleware=[Middleware(mock_middleware, arg=mock_middleware_arg)])  # type: ignore[list-item]
    async def handler() -> None:
        pass

    route = HTTPRoute(path="/", route_handlers=[handler])
    build_route_middleware_stack(app=Litestar(), route=route, route_handler=handler)
    ((_, kw_args),) = mock_middleware.call_args_list
    assert isinstance(kw_args["app"], ExceptionHandlerMiddleware)
    assert kw_args["arg"] is mock_middleware_arg
