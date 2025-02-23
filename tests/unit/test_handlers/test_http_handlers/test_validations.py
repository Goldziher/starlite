from pathlib import Path
from types import ModuleType
from typing import Annotated, Any, Callable

import pytest

from litestar import HttpMethod, Litestar, WebSocket, delete, get, patch, post, put, route
from litestar.exceptions import ImproperlyConfiguredException, ValidationException
from litestar.handlers.http_handlers import HTTPRouteHandler
from litestar.params import Body
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
        assert route(http_method=value)  # type: ignore[arg-type, truthy-function]

    # raises for invalid values
    with pytest.raises(ValidationException):
        HTTPRouteHandler(http_method="deleze", fn=lambda: None)  # type: ignore[arg-type]

    # also when passing an empty list
    with pytest.raises(ImproperlyConfiguredException):
        HTTPRouteHandler(http_method=[], status_code=HTTP_200_OK, fn=lambda: None)

    # also when passing malformed tokens
    with pytest.raises(ValidationException):
        HTTPRouteHandler(http_method=[HttpMethod.GET, "poft"], status_code=HTTP_200_OK, fn=lambda: None)  # type: ignore[list-item]


async def test_function_validation() -> None:
    with pytest.raises(ImproperlyConfiguredException, match="Missing return type annotation "):

        @get(path="/")
        def method_with_no_annotation():  # type: ignore[no-untyped-def]
            pass

        Litestar(route_handlers=[method_with_no_annotation])

    with pytest.raises(
        ImproperlyConfiguredException,
        match="A status code 204, 304 or in the range below 200 does not support a response body",
    ):

        @delete(path="/")
        def method_with_no_content() -> dict[str, str]:
            return {}

        Litestar(route_handlers=[method_with_no_content])

    with pytest.raises(
        ImproperlyConfiguredException,
        match="A status code 204, 304 or in the range below 200 does not support a response body",
    ):

        @get(path="/", status_code=HTTP_304_NOT_MODIFIED)
        def method_with_not_modified() -> dict[str, str]:
            return {}

        Litestar(route_handlers=[method_with_not_modified])

    with pytest.raises(
        ImproperlyConfiguredException,
        match="A status code 204, 304 or in the range below 200 does not support a response body",
    ):

        @get(path="/", status_code=HTTP_100_CONTINUE)
        def method_with_status_lower_than_200() -> dict[str, str]:
            return {}

        Litestar(route_handlers=[method_with_status_lower_than_200])

    @get(path="/", status_code=HTTP_307_TEMPORARY_REDIRECT)
    def redirect_method() -> Redirect:
        return Redirect("/test")

    Litestar(route_handlers=[redirect_method])

    @get(path="/")
    def file_method() -> File:
        return File(path=Path("."), filename="test_validations.py")

    Litestar(route_handlers=[file_method])

    assert not file_method.media_type

    with pytest.raises(ImproperlyConfiguredException, match="The 'socket' kwarg is not supported"):

        @get(path="/test")
        def test_function_1(socket: WebSocket) -> None:
            return None

        Litestar([test_function_1])

    with pytest.raises(ImproperlyConfiguredException, match="'data' kwarg is unsupported"):

        @get("/person")
        def test_function_2(self, data: DataclassPerson) -> None:  # type: ignore[no-untyped-def]
            return None

        Litestar(route_handlers=[test_function_2])


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


@pytest.mark.parametrize("decorator", [post, put, patch])
def test_body_param_with_non_bytes_annotation_raises(decorator: Callable[..., Any]) -> None:
    def handler_fn(body: list[str]) -> None:
        pass

    with pytest.raises(ImproperlyConfiguredException, match="Invalid type annotation for 'body' parameter"):
        Litestar([decorator()(handler_fn)])


@pytest.mark.parametrize("decorator", [post, put, patch])
def test_body_param_with_metadata_allowed(decorator: Callable[..., Any]) -> None:
    def handler_fn(body: Annotated[bytes, Body(title="something")]) -> None:
        pass

    # we expect no error here, even though the type isn't directly 'bytes' but has
    # metadata attached to it
    Litestar([decorator()(handler_fn)])
