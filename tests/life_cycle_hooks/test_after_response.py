from asyncio import sleep
from typing import TYPE_CHECKING, Dict

import pytest
from starlette.status import HTTP_200_OK

from starlite import Controller, Request, Router, get
from starlite.testing import create_test_client

state: Dict[str, str] = {}

if TYPE_CHECKING:
    from starlite.types import AfterResponseHandler


def create_sync_test_handler(msg: str) -> "AfterResponseHandler":
    def handler(_: Request) -> None:
        state["msg"] = msg

    return handler


def create_async_test_handler(msg: str) -> "AfterResponseHandler":
    async def handler(_: Request) -> None:
        await sleep(0.001)
        state["msg"] = msg

    return handler


@pytest.mark.parametrize("layer", ["app", "router", "controller", "handler"])
def test_after_response_resolution(layer: str) -> None:
    for handler in [create_sync_test_handler(layer), create_async_test_handler(layer)]:
        if state.get("msg"):
            del state["msg"]

        class MyController(Controller):
            path = "/controller"
            after_response = handler if layer == "controller" else None

            @get("/", after_response=handler if layer == "handler" else None)
            def my_handler(self) -> None:
                return None

        router = Router(
            path="/router", route_handlers=[MyController], after_response=handler if layer == "router" else None
        )

        with create_test_client(route_handlers=[router], after_response=handler if layer == "app" else None) as client:
            response = client.get("/router/controller/")
            assert response.status_code == HTTP_200_OK
            assert state["msg"] == layer
