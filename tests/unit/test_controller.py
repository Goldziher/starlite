from typing import Any

import msgspec
import pytest

from litestar import (
    Controller,
    HttpMethod,
    Litestar,
    Response,
    delete,
    get,
    patch,
    post,
    put,
    websocket,
)
from litestar.connection import WebSocket
from litestar.exceptions import ImproperlyConfiguredException
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.testing import create_test_client
from litestar.types import HTTPHandlerDecorator
from tests.models import DataclassPerson, DataclassPersonFactory


@pytest.mark.parametrize(
    "decorator, http_method, expected_status_code, return_value, return_annotation",
    [
        (
            get,
            HttpMethod.GET,
            HTTP_200_OK,
            Response(content=DataclassPersonFactory.build()),
            Response[DataclassPerson],
        ),
        (get, HttpMethod.GET, HTTP_200_OK, DataclassPersonFactory.build(), DataclassPerson),
        (post, HttpMethod.POST, HTTP_201_CREATED, DataclassPersonFactory.build(), DataclassPerson),
        (put, HttpMethod.PUT, HTTP_200_OK, DataclassPersonFactory.build(), DataclassPerson),
        (patch, HttpMethod.PATCH, HTTP_200_OK, DataclassPersonFactory.build(), DataclassPerson),
        (delete, HttpMethod.DELETE, HTTP_204_NO_CONTENT, None, None),
    ],
)
async def test_controller_http_method(
    decorator: HTTPHandlerDecorator,
    http_method: HttpMethod,
    expected_status_code: int,
    return_value: Any,
    return_annotation: Any,
) -> None:
    test_path = "/person"

    class MyController(Controller):
        path = test_path

        @decorator()
        def test_method(self) -> return_annotation:
            return return_value

    with create_test_client(MyController) as client:
        response = client.request(http_method, test_path)
        assert response.status_code == expected_status_code
        if return_value is not None and not isinstance(return_value, Response):
            assert response.json() == msgspec.to_builtins(return_value)


def test_controller_with_websocket_handler() -> None:
    test_path = "/person"

    class MyController(Controller):
        path = test_path

        @get()
        def get_person(self) -> DataclassPerson:
            return DataclassPersonFactory.build()

        @websocket(path="/socket")
        async def ws(self, socket: WebSocket) -> None:
            await socket.accept()
            await socket.send_json({"data": "123"})
            await socket.close()

    client = create_test_client(route_handlers=MyController)

    with client.websocket_connect(f"{test_path}/socket") as ws:
        ws.send_json({"data": "123"})
        data = ws.receive_json()
        assert data


def test_controller_validation() -> None:
    class BuggyController(Controller):
        path: str = "/ctrl"

        @get()
        async def handle_get(self) -> str:
            return "Hello World"

        @get()
        async def handle_get2(self) -> str:
            return "Hello World"

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[BuggyController])


def test_controller_subclassing() -> None:
    class BaseController(Controller):
        @get("/{id:int}")
        async def test_get(self, id: int) -> str:
            return f"{self.__class__.__name__} {id}"

    class FooController(BaseController):
        path = "/foo"

    class BarController(BaseController):
        path = "/bar"

    with create_test_client([FooController, BarController]) as client:
        response = client.get("/foo/123")
        assert response.status_code == 200
        assert response.text == "FooController 123"

        response = client.get("/bar/123")
        assert response.status_code == 200
        assert response.text == "BarController 123"
