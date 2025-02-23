from unittest.mock import Mock

import pytest

from litestar import Controller, Litestar, Request, Response, Router, get, post
from litestar.datastructures import ResponseHeader
from litestar.exceptions import ImproperlyConfiguredException
from litestar.types import Empty


def test_resolve_request_max_body_size() -> None:
    @post("/1")
    def router_handler() -> None:
        pass

    @post("/2")
    def app_handler() -> None:
        pass

    class MyController(Controller):
        request_max_body_size = 2

        @post("/3")
        def controller_handler(self) -> None:
            pass

    router = Router("/", route_handlers=[router_handler], request_max_body_size=1)
    app = Litestar(route_handlers=[app_handler, router, MyController], request_max_body_size=3)
    handler_1 = next(r for r in app.routes if r.path == "/1").route_handler_map["POST"]  # type: ignore[union-attr]
    handler_2 = next(r for r in app.routes if r.path == "/2").route_handler_map["POST"]  # type: ignore[union-attr]
    handler_3 = next(r for r in app.routes if r.path == "/3").route_handler_map["POST"]  # type: ignore[union-attr]
    assert handler_1.request_max_body_size == handler_1.resolve_request_max_body_size() == 1
    assert handler_2.request_max_body_size == handler_2.resolve_request_max_body_size() == 3
    assert handler_3.request_max_body_size == handler_3.resolve_request_max_body_size() == 2


def test_resolve_request_max_body_size_none() -> None:
    @post("/1", request_max_body_size=None)
    def router_handler() -> None:
        pass

    Litestar([router_handler])
    assert router_handler.request_max_body_size is None


def test_resolve_request_max_body_size_app_default() -> None:
    @post("/")
    def router_handler() -> None:
        pass

    app = Litestar(route_handlers=[router_handler])

    assert (
        next(r for r in app.routes if r.path == "/").route_handler_map["POST"].request_max_body_size  # type: ignore[union-attr]
        == app.request_max_body_size
        == 10_000_000
    )


def test_resolve_request_max_body_size_empty_on_all_layers_raises() -> None:
    @post("/")
    def handler_one() -> None:
        pass

    with pytest.raises(ImproperlyConfiguredException, match="'request_max_body_size' set to 'Empty'"):
        Litestar([handler_one], request_max_body_size=Empty)  # type: ignore[arg-type]


def test_resolve_request_class() -> None:
    @get()
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])
    assert app.route_handler_method_map["/"]["GET"].resolve_request_class() is Request  # type: ignore[attr-defined]


def test_resolve_response_class() -> None:
    @get()
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])
    assert app.route_handler_method_map["/"]["GET"].resolve_response_class() is Response  # type: ignore[attr-defined]


def test_resolve_response_headers() -> None:
    @get(response_headers={"foo": "bar"})
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])
    assert app.route_handler_method_map["/"]["GET"].resolve_response_headers() == frozenset(  # type: ignore[attr-defined]
        [ResponseHeader(name="foo", value="bar")]
    )


def test_resolve_before_request() -> None:
    before_request = Mock()

    @get(before_request=before_request)
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])
    resolved_handler = app.route_handler_method_map["/"]["GET"]
    assert resolved_handler.resolve_before_request() is resolved_handler.before_request  # type: ignore[attr-defined]


def test_resolve_after_response() -> None:
    after_response = Mock()

    @get(after_response=after_response)
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])
    resolved_handler = app.route_handler_method_map["/"]["GET"]
    assert resolved_handler.resolve_after_response() is resolved_handler.after_response  # type: ignore[attr-defined]


def test_resolve_include_in_schema() -> None:
    @get(include_in_schema=False)
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])
    assert app.route_handler_method_map["/"]["GET"].resolve_include_in_schema() is False  # type: ignore[attr-defined]


def test_resolve_security() -> None:
    security = [{"foo": ["bar"]}]

    @get(security=security)
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])
    resolved_handler = app.route_handler_method_map["/"]["GET"]
    assert resolved_handler.resolve_security() == resolved_handler.security  # type: ignore[attr-defined]


def test_resolve_tags() -> None:
    @get(tags=["foo"])
    async def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])
    resolved_handler = app.route_handler_method_map["/"]["GET"]
    assert resolved_handler.resolve_tags() == resolved_handler.tags  # type: ignore[attr-defined]
