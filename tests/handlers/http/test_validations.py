from pathlib import Path
from sys import version_info
from typing import Dict

import pytest
from pydantic import ValidationError

from starlite import HttpMethod, MediaType, Response, WebSocket, delete, get, route
from starlite.exceptions import ImproperlyConfiguredException, ValidationException
from starlite.handlers.http_handlers import HTTPRouteHandler
from starlite.response_containers import File, Redirect
from starlite.status_codes import (
    HTTP_100_CONTINUE,
    HTTP_200_OK,
    HTTP_304_NOT_MODIFIED,
    HTTP_307_TEMPORARY_REDIRECT,
)
from tests import Person


def test_route_handler_validation_http_method() -> None:
    # doesn't raise for http methods
    for value in (*list(HttpMethod), *list(map(lambda x: x.upper(), list(HttpMethod)))):  # noqa: C417
        assert route(http_method=value)  # type: ignore

    expected_validation_exception = ValidationException if version_info < (3, 9) else ValidationError

    # raises for invalid values
    with pytest.raises(expected_validation_exception):
        HTTPRouteHandler(http_method="deleze")  # type: ignore

    # also when passing an empty list
    with pytest.raises(ImproperlyConfiguredException):
        route(http_method=[], status_code=HTTP_200_OK)

    # also when passing malformed tokens
    with pytest.raises(expected_validation_exception):
        route(http_method=[HttpMethod.GET, "poft"], status_code=HTTP_200_OK)  # type: ignore


@pytest.mark.skipif(version_info < (3, 9), reason="validate_arguments disabled below 3.9")
def test_route_handler_validation_response_class() -> None:
    # doesn't raise when subclass of starlette response is passed
    class SpecialResponse(Response):
        pass

    assert HTTPRouteHandler(http_method=HttpMethod.GET, response_class=SpecialResponse)

    # raises otherwise
    with pytest.raises(ValidationError):
        HTTPRouteHandler(http_method=HttpMethod.GET, response_class={})  # type: ignore


async def test_function_validation(anyio_backend: str) -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @get(path="/")
        def method_with_no_annotation():  # type: ignore
            pass

    with pytest.raises(ValidationException):

        @get(path="/", status_code=HTTP_200_OK)
        def redirect_method_without_proper_status() -> Redirect:
            return Redirect(path="/redirected")

    with pytest.raises(ImproperlyConfiguredException):

        @delete(path="/")
        def method_with_no_content() -> Dict[str, str]:
            return {}

    with pytest.raises(ImproperlyConfiguredException):

        @get(path="/", status_code=HTTP_304_NOT_MODIFIED)
        def method_with_not_modified() -> Dict[str, str]:
            return {}

    with pytest.raises(ImproperlyConfiguredException):

        @get(path="/", status_code=HTTP_100_CONTINUE)
        def method_with_status_lower_than_200() -> Dict[str, str]:
            return {}

    @get(path="/", status_code=HTTP_307_TEMPORARY_REDIRECT)
    def redirect_method() -> Redirect:
        return Redirect("/test")  # type: ignore

    @get(path="/")
    def file_method() -> File:
        return File(path=Path("."), filename="test_validations.py")

    assert file_method.media_type == MediaType.TEXT

    with pytest.raises(ImproperlyConfiguredException):

        @get(path="/test")
        def test_function_1(socket: WebSocket) -> None:
            return None

    with pytest.raises(ImproperlyConfiguredException):

        @get("/person")
        def test_function_2(self, data: Person) -> None:  # type: ignore
            return None
