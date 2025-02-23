from asyncio import sleep
from typing import TYPE_CHECKING, Any

import pytest

from litestar import Controller, get
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from litestar.connection import Request
    from litestar.datastructures.state import State


def router_first_dependency() -> bool:
    return True


async def router_second_dependency() -> bool:
    await sleep(0)
    return False


def controller_first_dependency(headers: dict[str, Any]) -> dict[Any, Any]:
    assert headers
    return {}


async def controller_second_dependency(request: "Request[Any, Any, State]") -> dict[Any, Any]:
    assert request
    await sleep(0)
    return {}


def local_method_first_dependency(query_param: int) -> int:
    assert isinstance(query_param, int)
    return query_param


def local_method_second_dependency(path_param: str) -> str:
    assert isinstance(path_param, str)
    return path_param


test_path = "/test"


@pytest.fixture
def first_controller() -> type[Controller]:
    class FirstController(Controller):
        path = test_path
        dependencies = {
            "first": Provide(controller_first_dependency, sync_to_thread=False),
            "second": Provide(controller_second_dependency),
        }

        @get(
            path="/{path_param:str}",
            dependencies={
                "first": Provide(local_method_first_dependency, sync_to_thread=False),
            },
        )
        def test_method(self, first: int, second: dict[Any, Any], third: bool) -> None:
            assert isinstance(first, int)
            assert isinstance(second, dict)
            assert not third

    return FirstController


def test_controller_dependency_injection(first_controller: type[Controller]) -> None:
    with create_test_client(
        first_controller,
        dependencies={
            "second": Provide(router_first_dependency, sync_to_thread=False),
            "third": Provide(router_second_dependency),
        },
    ) as client:
        response = client.get(f"{test_path}/abcdef?query_param=12345")
        assert response.status_code == HTTP_200_OK


def test_function_dependency_injection() -> None:
    @get(
        path=test_path + "/{path_param:str}",
        dependencies={
            "first": Provide(local_method_first_dependency, sync_to_thread=False),
            "third": Provide(local_method_second_dependency, sync_to_thread=False),
        },
    )
    def test_function(first: int, second: bool, third: str) -> None:
        assert isinstance(first, int)
        assert second is False
        assert isinstance(third, str)

    with create_test_client(
        test_function,
        dependencies={
            "first": Provide(router_first_dependency, sync_to_thread=False),
            "second": Provide(router_second_dependency),
        },
    ) as client:
        response = client.get(f"{test_path}/abcdef?query_param=12345")
        assert response.status_code == HTTP_200_OK


def test_dependency_isolation(first_controller: type[Controller]) -> None:
    class SecondController(Controller):
        path = "/second"

        @get()
        def test_method(self, first: dict[Any, Any]) -> None:
            pass

    with create_test_client([first_controller, SecondController]) as client:
        response = client.get("/second")
        assert response.status_code == HTTP_400_BAD_REQUEST
