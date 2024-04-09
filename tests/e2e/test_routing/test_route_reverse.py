from datetime import time
from typing import Type

import pytest

from litestar import Litestar, Router, delete, get, patch, post, put
from litestar.exceptions import NoRouteMatchFoundException
from litestar.handlers.http_handlers import HTTPRouteHandler


@pytest.mark.parametrize("decorator", [get, post, patch, put, delete])
def test_route_reverse(decorator: Type[HTTPRouteHandler]) -> None:
    @decorator("/path-one/{param:str}", name="handler-name")  # type: ignore[call-arg]
    def handler() -> None:
        return None

    @decorator("/path-two", name="handler-no-params")  # type: ignore[call-arg]
    def handler_no_params() -> None:
        return None

    @decorator("/multiple/{str_param:str}/params/{int_param:int}/", name="multiple-params-handler-name")  # type: ignore[call-arg]
    def handler2() -> None:
        return None

    @decorator(
        ["/handler3", "/handler3/{str_param:str}/", "/handler3/{str_param:str}/{int_param:int}/"],
        name="multiple-default-params",
    )  # type: ignore[call-arg]
    def handler3(str_param: str = "default", int_param: int = 0) -> None:
        return None

    @decorator(["/handler4/int/{int_param:int}", "/handler4/str/{str_param:str}"], name="handler4")  # type: ignore[call-arg]
    def handler4(int_param: int = 1, str_param: str = "str") -> None:
        return None

    router = Router("router-path/", route_handlers=[handler, handler_no_params, handler3, handler4])
    router_with_param = Router("router-with-param/{router_param:str}", route_handlers=[handler2])
    app = Litestar(route_handlers=[router, router_with_param])

    reversed_url_path = app.route_reverse("handler-name", param="param-value")
    assert reversed_url_path == "/router-path/path-one/param-value"

    reversed_url_path = app.route_reverse("handler-no-params")
    assert reversed_url_path == "/router-path/path-two"

    reversed_url_path = app.route_reverse(
        "multiple-params-handler-name", router_param="router", str_param="abc", int_param=123
    )
    assert reversed_url_path == "/router-with-param/router/multiple/abc/params/123"

    reversed_url_path = app.route_reverse("handler4", int_param=100)
    assert reversed_url_path == "/router-path/handler4/int/100"

    reversed_url_path = app.route_reverse("handler4", str_param="string")
    assert reversed_url_path == "/router-path/handler4/str/string"

    with pytest.raises(NoRouteMatchFoundException):
        reversed_url_path = app.route_reverse("nonexistent-handler")


@pytest.mark.parametrize(
    "complex_path_param",
    [("time", time(hour=14), "14:00"), ("float", float(1 / 3), "0.33")],
)
def test_route_reverse_validation_complex_params(complex_path_param) -> None:  # type: ignore[no-untyped-def]
    param_type, param_value, param_manual_str = complex_path_param

    @get(f"/abc/{{param:{param_type}}}", name="handler")
    def handler() -> None:
        pass

    app = Litestar(route_handlers=[handler])

    # test that complex types of path params accept either itself
    # or string but nothing else
    with pytest.raises(NoRouteMatchFoundException):
        app.route_reverse("handler", param=123)

    reversed_url_path = app.route_reverse("handler", param=param_manual_str)
    assert reversed_url_path == f"/abc/{param_manual_str}"

    reversed_url_path = app.route_reverse("handler", param=param_value)
    assert reversed_url_path == f"/abc/{param_value}"


def test_route_reverse_validation() -> None:
    @get("/abc/{param:int}", name="handler-name")
    def handler_one() -> None:
        pass

    @get("/def/{param:str}", name="another-handler-name")
    def handler_two() -> None:
        pass

    app = Litestar(route_handlers=[handler_one, handler_two])

    with pytest.raises(NoRouteMatchFoundException):
        app.route_reverse("handler-name")

    with pytest.raises(NoRouteMatchFoundException):
        app.route_reverse("handler-name", param="str")

    with pytest.raises(NoRouteMatchFoundException):
        app.route_reverse("another-handler-name", param=1)
