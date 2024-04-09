from typing import TYPE_CHECKING, Type

import pytest

from litestar import Controller, Request, Response, Router, get
from litestar.exceptions import (
    HTTPException,
    InternalServerException,
    NotFoundException,
    ServiceUnavailableException,
    ValidationException,
)
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from litestar.types import ExceptionHandler


@pytest.mark.parametrize(
    ["exc_to_raise", "expected_layer"],
    [
        (ValidationException, "router"),
        (InternalServerException, "controller"),
        (ServiceUnavailableException, "handler"),
        (NotFoundException, "handler"),
    ],
)
def test_exception_handling(exc_to_raise: HTTPException, expected_layer: str) -> None:
    caller = {"name": ""}

    def create_named_handler(caller_name: str, expected_exception: Type[Exception]) -> "ExceptionHandler":
        def handler(req: Request, exc: Exception) -> Response:
            assert isinstance(exc, expected_exception)
            assert isinstance(req, Request)
            caller["name"] = caller_name
            return Response(content={}, status_code=exc_to_raise.status_code)

        return handler

    class ControllerWithHandler(Controller):
        path = "/test"
        exception_handlers = {
            InternalServerException: create_named_handler("controller", InternalServerException),
            ServiceUnavailableException: create_named_handler("controller", ServiceUnavailableException),
        }

        @get(
            "/",
            exception_handlers={
                ServiceUnavailableException: create_named_handler("handler", ServiceUnavailableException),
                NotFoundException: create_named_handler("handler", NotFoundException),
            },
        )
        def my_handler(self) -> None:
            raise exc_to_raise

    my_router = Router(
        path="/base",
        route_handlers=[ControllerWithHandler],
        exception_handlers={
            InternalServerException: create_named_handler("router", InternalServerException),
            ValidationException: create_named_handler("router", ValidationException),
        },
    )

    with create_test_client(route_handlers=[my_router]) as client:
        response = client.get("/base/test/")
        assert response.status_code == exc_to_raise.status_code, response.json()
        assert caller["name"] == expected_layer


def test_exception_handler_with_custom_request_class() -> None:
    class CustomRequest(Request): ...

    def handler(req: Request, exc: Exception) -> Response:
        assert isinstance(req, CustomRequest)

        return Response(content={})

    @get()
    async def index() -> None:
        _ = 1 / 0

    with create_test_client([index], exception_handlers={Exception: handler}, request_class=CustomRequest) as client:
        client.get("/")
