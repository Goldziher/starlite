from asyncio import sleep
from typing import Any

import pytest

from litestar import Controller, websocket
from litestar.connection import WebSocket
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import WebSocketDisconnect
from litestar.testing import create_test_client


def router_first_dependency() -> bool:
    return True


async def router_second_dependency() -> bool:
    await sleep(0)
    return False


def controller_first_dependency(headers: dict[str, Any]) -> dict[Any, Any]:
    assert headers
    return {}


async def controller_second_dependency(socket: WebSocket[Any, Any, Any]) -> dict[Any, Any]:
    assert socket
    await sleep(0)
    return {}


def local_method_first_dependency(query_param: int) -> int:
    assert isinstance(query_param, int)
    return query_param


def local_method_second_dependency(path_param: str) -> str:
    assert isinstance(path_param, str)
    return path_param


test_path = "/test"


class FirstController(Controller):
    path = test_path
    dependencies = {
        "first": Provide(controller_first_dependency, sync_to_thread=True),
        "second": Provide(controller_second_dependency),
    }

    @websocket(
        path="/{path_param:str}",
        dependencies={
            "first": Provide(local_method_first_dependency, sync_to_thread=False),
        },
    )
    async def test_method(
        self, socket: WebSocket[Any, Any, Any], first: int, second: dict[Any, Any], third: bool
    ) -> None:
        await socket.accept()
        msg = await socket.receive_json()
        assert msg
        assert socket
        assert isinstance(first, int)
        assert isinstance(second, dict)
        assert not third
        await socket.close()


def test_controller_dependency_injection() -> None:
    client = create_test_client(
        FirstController,
        dependencies={
            "second": Provide(router_first_dependency, sync_to_thread=False),
            "third": Provide(router_second_dependency),
        },
    )
    with client.websocket_connect(f"{test_path}/abcdef?query_param=12345") as ws:
        ws.send_json({"data": "123"})


def test_function_dependency_injection() -> None:
    @websocket(
        path=test_path + "/{path_param:str}",
        dependencies={
            "first": Provide(local_method_first_dependency, sync_to_thread=False),
            "third": Provide(local_method_second_dependency, sync_to_thread=False),
        },
    )
    async def test_function(socket: WebSocket[Any, Any, State], first: int, second: bool, third: str) -> None:
        await socket.accept()
        assert socket
        msg = await socket.receive_json()
        assert msg
        assert isinstance(first, int)
        assert second is False
        assert isinstance(third, str)
        await socket.close()

    client = create_test_client(
        test_function,
        dependencies={
            "first": Provide(router_first_dependency, sync_to_thread=False),
            "second": Provide(router_second_dependency),
        },
    )
    with client.websocket_connect(f"{test_path}/abcdef?query_param=12345") as ws:
        ws.send_json({"data": "123"})


def test_dependency_isolation() -> None:
    class SecondController(Controller):
        path = "/second"

        @websocket()
        async def test_method(self, socket: WebSocket[Any, Any, Any], _: dict[Any, Any]) -> None:
            await socket.accept()

    client = create_test_client([FirstController, SecondController])
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/second/abcdef?query_param=12345") as ws:
        ws.send_json({"data": "123"})
