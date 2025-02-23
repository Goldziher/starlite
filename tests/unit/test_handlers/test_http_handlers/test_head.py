from pathlib import Path
from typing import Generic, TypeVar

import pytest

from litestar import Litestar, Response, head
from litestar.exceptions import ImproperlyConfiguredException
from litestar.response.file import ASGIFileResponse, File
from litestar.routes import HTTPRoute
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


def test_head_decorator() -> None:
    @head("/")
    def handler() -> None:
        return

    with create_test_client(handler) as client:
        response = client.head("/")
        assert response.status_code == HTTP_200_OK


def test_head_decorator_raises_validation_error_if_body_is_declared() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @head("/")
        def handler() -> dict:
            return {}

        handler.on_registration(HTTPRoute(path="/", route_handlers=[handler]), app=Litestar())


def test_head_decorator_none_response_return_value_allowed() -> None:
    # https://github.com/litestar-org/litestar/issues/3640
    T = TypeVar("T")

    class MyResponse(Generic[T], Response[T]):
        pass

    @head("/")
    def handler() -> Response[None]:
        return Response(None)

    Litestar([handler])

    @head("/")
    def handler_subclass() -> MyResponse[None]:
        return MyResponse(None)

    Litestar([handler_subclass])


def test_head_decorator_does_not_raise_for_file_response() -> None:
    @head("/")
    def handler() -> "File":
        return File("test_to_response.py")

    Litestar(route_handlers=[handler])


def test_head_decorator_does_not_raise_for_asgi_file_response() -> None:
    @head("/")
    def handler() -> ASGIFileResponse:
        return ASGIFileResponse(file_path=Path("test_head.py"))

    Litestar(route_handlers=[handler])
