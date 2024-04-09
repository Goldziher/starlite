from typing import Dict

import pytest

from litestar import Controller, HttpMethod, Litestar, Router, get, post
from litestar.datastructures import CacheControlHeader, ETag, ResponseHeader
from litestar.datastructures.headers import Header
from litestar.status_codes import HTTP_201_CREATED
from litestar.testing import TestClient, create_test_client


def test_response_headers() -> None:
    router_first = ResponseHeader(name="second", value="1")
    router_second = ResponseHeader(name="third", value="2")
    controller_first = ResponseHeader(name="first", value="3")
    controller_second = ResponseHeader(name="second", value="4")
    app_first = ResponseHeader(name="first", value="5")
    app_second = ResponseHeader(name="fourth", value="6")
    local_first = ResponseHeader(name="first", value="7")

    test_path = "/test"

    class MyController(Controller):
        path = test_path
        response_headers = [controller_first, controller_second]

        @get(path="/{path_param:str}", response_headers=[local_first])
        def test_method(self) -> None:
            pass

    first_router = Router(path="/users", response_headers=[router_first, router_second], route_handlers=[MyController])
    second_router = Router(
        path="/external", response_headers=[ResponseHeader(name="external", value="nope")], route_handlers=[]
    )
    app = Litestar(
        openapi_config=None,
        response_headers=[app_first, app_second],
        route_handlers=[first_router, second_router],
    )

    route_handler, _ = app.routes[0].route_handler_map[HttpMethod.GET]  # type: ignore[union-attr]
    resolved_headers = {header.name: header for header in route_handler.resolve_response_headers()}
    assert resolved_headers["first"].value == local_first.value
    assert resolved_headers["second"].value == controller_second.value
    assert resolved_headers["third"].value == router_second.value
    assert resolved_headers["fourth"].value == app_second.value
    assert "external" not in resolved_headers


def test_response_headers_mapping() -> None:
    @get(response_headers={"foo": "bar"})
    def handler_one() -> None:
        pass

    @get(response_headers=[ResponseHeader(name="foo", value="bar")])
    def handler_two() -> None:
        pass

    assert handler_one.resolve_response_headers() == handler_two.resolve_response_headers()


def test_response_headers_mapping_unresolved() -> None:
    # this should never happen, as there's no way to create this situation which type-checks.
    # we test for it nevertheless

    @get()
    def handler_one() -> None:
        pass

    handler_one.response_headers = {"foo": "bar"}  # type: ignore[assignment]

    assert handler_one.resolve_response_headers() == frozenset([ResponseHeader(name="foo", value="bar")])


def test_response_headers_rendering() -> None:
    @post(
        path="/test",
        tags=["search"],
        response_headers=[ResponseHeader(name="test-header", value="test value", description="test")],
    )
    def my_handler(data: Dict[str, str]) -> Dict[str, str]:
        return data

    with create_test_client(my_handler) as client:
        response = client.post("/test", json={"hello": "world"})
        assert response.status_code == HTTP_201_CREATED
        assert response.headers.get("test-header") == "test value"


@pytest.mark.parametrize(
    "config_kwarg,app_header,controller_header,handler_header",
    [
        (
            "etag",
            ETag(value="1"),
            ETag(value="2"),
            ETag(value="3"),
        ),
        (
            "cache_control",
            CacheControlHeader(max_age=1),
            CacheControlHeader(max_age=2),
            CacheControlHeader(max_age=3),
        ),
    ],
)
def test_explicit_response_headers(
    config_kwarg: str, app_header: Header, controller_header: Header, handler_header: Header
) -> None:
    class MyController(Controller):
        @get(
            path="/handler-override",
            **{config_kwarg: handler_header},  # type: ignore[arg-type]
        )
        def controller_override(self) -> None:
            pass

        @get(path="/controller")
        def controller_handler(self) -> None:
            pass

    setattr(MyController, config_kwarg, controller_header)

    @get(path="/app")
    def app_handler() -> None:
        pass

    app = Litestar(
        route_handlers=[MyController, app_handler],
        **{config_kwarg: app_header},  # type: ignore[arg-type]
    )

    with TestClient(app=app) as client:
        for path, expected_value in {
            "handler-override": handler_header,
            "controller": controller_header,
            "app": app_header,
        }.items():
            response = client.get(path)
            assert response.headers[expected_value.HEADER_NAME] == expected_value.to_header()


@pytest.mark.parametrize(
    "config_kwarg,header",
    [
        ("cache_control", CacheControlHeader(no_cache=True, documentation_only=True)),
        ("etag", ETag(value="1", documentation_only=True)),
    ],
)
def test_explicit_headers_documentation_only(config_kwarg: str, header: Header) -> None:
    @get(
        path="/test",
        **{config_kwarg: header},  # type: ignore[arg-type]
    )
    def my_handler() -> None:
        pass

    with create_test_client(my_handler) as client:
        response = client.get("/test")
        assert header.HEADER_NAME not in response.headers


@pytest.mark.parametrize(
    "config_kwarg,response_header,header",
    [
        (
            "cache_control",
            ResponseHeader(name=CacheControlHeader.HEADER_NAME, value="no-store"),
            CacheControlHeader(no_cache=True),
        ),
        ("etag", ResponseHeader(name=ETag.HEADER_NAME, value="1"), ETag(value="2")),
    ],
)
def test_explicit_headers_override_response_headers(
    config_kwarg: str, response_header: ResponseHeader, header: Header
) -> None:
    @get(
        path="/test",
        response_headers=[response_header],
        **{config_kwarg: header},  # type: ignore[arg-type]
    )
    def my_handler() -> None:
        pass

    app = Litestar(route_handlers=[my_handler])

    route_handler, _ = app.routes[0].route_handler_map[HttpMethod.GET]  # type: ignore[union-attr]
    resolved_headers = {header.name: header for header in route_handler.resolve_response_headers()}
    assert resolved_headers[header.HEADER_NAME].value == header.to_header()
