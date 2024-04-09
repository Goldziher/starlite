from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock
from uuid import UUID, uuid1, uuid4

import pytest

from litestar import Litestar, MediaType, get, post
from litestar.exceptions import ImproperlyConfiguredException
from litestar.params import Parameter
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client


@pytest.mark.parametrize(
    "params_dict,should_raise",
    [
        (
            {
                "version": 1.0,
                "service_id": 1,
                "user_id": "abc",
                "order_id": str(uuid4()),
            },
            False,
        ),
        (
            {
                "version": 4.1,
                "service_id": 1,
                "user_id": "abc",
                "order_id": str(uuid4()),
            },
            True,
        ),
        (
            {
                "version": 0.2,
                "service_id": 101,
                "user_id": "abc",
                "order_id": str(uuid4()),
            },
            True,
        ),
        (
            {
                "version": 0.2,
                "service_id": 1,
                "user_id": "abcdefghijklm",
                "order_id": str(uuid4()),
            },
            True,
        ),
        (
            {
                "version": 0.2,
                "service_id": 1,
                "user_id": "abc",
                "order_id": str(uuid1()),
            },
            False,
        ),
    ],
)
def test_path_params(params_dict: dict, should_raise: bool) -> None:
    test_path = "{version:float}/{service_id:int}/{user_id:str}/{order_id:uuid}"

    @get(path=test_path)
    def test_method(
        order_id: UUID,
        version: float = Parameter(gt=0.1, le=4.0),
        service_id: int = Parameter(gt=0, le=100),
        user_id: str = Parameter(min_length=1, max_length=10),
    ) -> None:
        assert version
        assert service_id
        assert user_id
        assert order_id

    with create_test_client(test_method) as client:
        response = client.get(
            f"{params_dict['version']}/{params_dict['service_id']}/{params_dict['user_id']}/{params_dict['order_id']}"
        )
        if should_raise:
            assert response.status_code == HTTP_400_BAD_REQUEST, response.json()
        else:
            assert response.status_code == HTTP_200_OK, response.json()


@pytest.mark.parametrize(
    "path",
    [
        "/{param}",
        "/{param:foo}",
        "/{param:int:int}",
        "/{:int}",
        "/{param:}",
        "/{  :int}",
        "/{:}",
        "/{::}",
        "/{}",
    ],
)
def test_path_param_validation(path: str) -> None:
    @get(path=path)
    def test_method() -> None:
        raise AssertionError("should not be called")

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[test_method])


def test_duplicate_path_param_validation() -> None:
    @get(path="/{param:int}/foo/{param:int}")
    def test_method() -> None:
        raise AssertionError("should not be called")

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[test_method])


def test_path_param_defined_in_layered_params_error() -> None:
    @get(path="/{param:int}")
    def test_method(param: int) -> None:
        raise AssertionError("should not be called")

    with pytest.raises(ImproperlyConfiguredException) as exc_info:
        Litestar(route_handlers=[test_method], parameters={"param": Parameter(gt=3)})

    assert "Kwarg resolution ambiguity detected for the following keys: param." in str(exc_info.value)


@pytest.mark.parametrize(
    "param_type_name, param_type_class, value, expected_value",
    [
        ["str", str, "abc", "abc"],
        ["int", int, "1", 1],
        ["float", float, "1.01", 1.01],
        ["uuid", UUID, "0fcb1054c56e4dd4a127f70a97d1fc21", UUID("0fcb1054c56e4dd4a127f70a97d1fc21")],
        ["uuid", UUID, "542226d1-7199-41a0-9cba-aaa6d85932a3", UUID("542226d1-7199-41a0-9cba-aaa6d85932a3")],
        ["decimal", Decimal, "1.00001", Decimal("1.00001")],
        ["date", date, "2023-07-15", date(year=2023, month=7, day=15)],
        ["time", time, "01:02:03", time(1, 2, 3)],
        ["datetime", datetime, "2023-07-15T15:45:34.073314", datetime.fromisoformat("2023-07-15T15:45:34.073314")],
        ["timedelta", timedelta, "86400.0", timedelta(days=1)],
        ["timedelta", timedelta, "P1D", timedelta(days=1)],
        ["timedelta", timedelta, "PT1H1S", timedelta(hours=1, seconds=1)],
        ["path", Path, "/1/2/3/4/some-file.txt", Path("/1/2/3/4/some-file.txt")],
        ["path", Path, "1/2/3/4/some-file.txt", Path("/1/2/3/4/some-file.txt")],
    ],
)
def test_path_param_type_resolution(
    param_type_name: str, param_type_class: Any, value: str, expected_value: Any
) -> None:
    mock = MagicMock()

    @get("/some/test/path/{test:" + param_type_name + "}")
    def handler(test: param_type_class) -> None:
        mock(test)

    with create_test_client(handler) as client:
        response = client.get(f"/some/test/path/{value}")

    assert response.status_code == HTTP_200_OK
    mock.assert_called_once_with(expected_value)


def test_differently_named_path_params_on_same_level() -> None:
    @get("/{name:str}", media_type=MediaType.TEXT)
    def get_greeting(name: str) -> str:
        return f"Hello, {name}!"

    @post("/{title:str}", media_type=MediaType.TEXT)
    def post_greeting(title: str) -> str:
        return f"Hello, {title}!"

    with create_test_client(route_handlers=[get_greeting, post_greeting]) as client:
        response = client.get("/Moishe")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Hello, Moishe!"
        response = client.post("/Moishe")
        assert response.status_code == HTTP_201_CREATED
        assert response.text == "Hello, Moishe!"


def test_optional_path_parameter() -> None:
    @get(path=["/", "/{message:str}"], media_type=MediaType.TEXT, sync_to_thread=False)
    def handler(message: Optional[str]) -> str:
        return message or "no message"

    with create_test_client(route_handlers=[handler]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "no message"
        response = client.get("/hello")
        assert response.status_code == HTTP_200_OK
        assert response.text == "hello"
