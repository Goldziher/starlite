from datetime import date, datetime, time, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from litestar import Litestar, Router, delete, get, patch, post, put
from litestar.exceptions import NoRouteMatchFoundException
from litestar.types import HTTPHandlerDecorator


@pytest.mark.parametrize("decorator", [get, post, patch, put, delete])
def test_route_reverse(decorator: HTTPHandlerDecorator) -> None:
    @decorator("/path-one/{param:str}", name="handler-name")
    def handler() -> None:
        return None

    @decorator("/path-two", name="handler-no-params")
    def handler_no_params() -> None:
        return None

    @decorator("/multiple/{str_param:str}/params/{int_param:int}/", name="multiple-params-handler-name")
    def handler2() -> None:
        return None

    @decorator(
        ["/handler3", "/handler3/{str_param:str}/", "/handler3/{str_param:str}/{int_param:int}/"],
        name="multiple-default-params",
    )
    def handler3(str_param: str = "default", int_param: int = 0) -> None:
        return None

    @decorator(["/handler4/int/{int_param:int}", "/handler4/str/{str_param:str}"], name="handler4")
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


def test_route_reverse_allow_string_params() -> None:
    @get(
        "/strings-everywhere/{datetime_param:datetime}/{date_param:date}/"
        "{time_param:time}/{timedelta_param:timedelta}/"
        "{float_param:float}/{uuid_param:uuid}/{path_param:path}",
        name="strings-everywhere-handler",
    )
    def strings_everywhere_handler(
        datetime_param: datetime,
        date_param: date,
        time_param: time,
        timedelta_param: timedelta,
        float_param: float,
        uuid_param: UUID,
        path_param: Path,
    ) -> None:
        return None

    app = Litestar(route_handlers=[strings_everywhere_handler])

    reversed_url_path = app.route_reverse(
        "strings-everywhere-handler",
        datetime_param="0001-01-01T01:01:01.000001Z",  # datetime(1, 1, 1, 1, 1, 1, 1, tzinfo=UTC)
        date_param="0001-01-01",  # date(1,1,1)
        time_param="01:01:01.000001Z",  # time(1, 1, 1, 1, tzinfo=UTC)
        timedelta_param="P8DT3661.001001S",  # timedelta(1, 1, 1, 1, 1, 1, 1)
        float_param="0.1",
        uuid_param="00000000-0000-0000-0000-000000000000",  # UUID(int=0)
        path_param="/home/user",  # Path("/home/user/"),
    )

    assert (
        reversed_url_path == "/strings-everywhere/0001-01-01T01:01:01.000001Z/"
        "0001-01-01/01:01:01.000001Z/P8DT3661.001001S/0.1/"
        "00000000-0000-0000-0000-000000000000/home/user"
    )
