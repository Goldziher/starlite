from pathlib import Path
from types import ModuleType
from typing import Callable, Dict

import pytest

from litestar import HttpMethod, Litestar, WebSocket, delete, get, route
from litestar.exceptions import ImproperlyConfiguredException, ValidationException
from litestar.handlers.http_handlers import HTTPRouteHandler
from litestar.response import File, Redirect
from litestar.status_codes import (
    HTTP_100_CONTINUE,
    HTTP_200_OK,
    HTTP_304_NOT_MODIFIED,
    HTTP_307_TEMPORARY_REDIRECT,
)
from tests.models import DataclassPerson


def test_route_handler_validation_http_method() -> None:
    # doesn't raise for http methods
    for value in (*list(HttpMethod), *[x.upper() for x in list(HttpMethod)]):
        assert route(http_method=value)  # type: ignore[arg-type, truthy-bool]

    # raises for invalid values
    with pytest.raises(ValidationException):
        HTTPRouteHandler(http_method="deleze")  # type: ignore[arg-type]

    # also when passing an empty list
    with pytest.raises(ImproperlyConfiguredException):
        route(http_method=[], status_code=HTTP_200_OK)

    # also when passing malformed tokens
    with pytest.raises(ValidationException):
        route(http_method=[HttpMethod.GET, "poft"], status_code=HTTP_200_OK)  # type: ignore[list-item]


async def test_function_validation() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @get(path="/")
        def method_with_no_annotation():  # type: ignore[no-untyped-def]
            pass

        Litestar(route_handlers=[method_with_no_annotation])

        method_with_no_annotation.on_registration(Litestar())

    with pytest.raises(ImproperlyConfiguredException):

        @delete(path="/")
        def method_with_no_content() -> Dict[str, str]:
            return {}

        Litestar(route_handlers=[method_with_no_content])

        method_with_no_content.on_registration(Litestar())

    with pytest.raises(ImproperlyConfiguredException):

        @get(path="/", status_code=HTTP_304_NOT_MODIFIED)
        def method_with_not_modified() -> Dict[str, str]:
            return {}

        Litestar(route_handlers=[method_with_not_modified])

        method_with_not_modified.on_registration(Litestar())

    with pytest.raises(ImproperlyConfiguredException):

        @get(path="/", status_code=HTTP_100_CONTINUE)
        def method_with_status_lower_than_200() -> Dict[str, str]:
            return {}

        Litestar(route_handlers=[method_with_status_lower_than_200])

        method_with_status_lower_than_200.on_registration(Litestar())

    @get(path="/", status_code=HTTP_307_TEMPORARY_REDIRECT)
    def redirect_method() -> Redirect:
        return Redirect("/test")

    Litestar(route_handlers=[redirect_method])

    redirect_method.on_registration(Litestar())

    @get(path="/")
    def file_method() -> File:
        return File(path=Path("."), filename="test_validations.py")

    Litestar(route_handlers=[file_method])

    file_method.on_registration(Litestar())

    assert not file_method.media_type

    with pytest.raises(ImproperlyConfiguredException):

        @get(path="/test")
        def test_function_1(socket: WebSocket) -> None:
            return None

        test_function_1.on_registration(Litestar())

    with pytest.raises(ImproperlyConfiguredException):

        @get("/person")
        def test_function_2(self, data: DataclassPerson) -> None:  # type: ignore[no-untyped-def]
            return None

        Litestar(route_handlers=[test_function_2])

        test_function_2.on_registration(Litestar())


@pytest.mark.parametrize(
    ("return_annotation", "should_raise"),
    [
        ("None", False),
        ("Response[None]", False),
        ("int", True),
        ("Response[int]", True),
        ("Response", True),
    ],
)
def test_204_response_annotations(
    return_annotation: str, should_raise: bool, create_module: Callable[[str], ModuleType]
) -> None:
    module = create_module(
        f"""
from litestar import get
from litestar.response import Response
from litestar.status_codes import HTTP_204_NO_CONTENT

@get(path="/", status_code=HTTP_204_NO_CONTENT)
def no_response_handler() -> {return_annotation}:
    pass
"""
    )

    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            Litestar(route_handlers=[module.no_response_handler])
        return

    Litestar(route_handlers=[module.no_response_handler])
