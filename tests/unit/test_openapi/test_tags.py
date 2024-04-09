from typing import TYPE_CHECKING, Any, Type

import pytest

from litestar import Controller, Litestar, Router, get
from litestar.handlers.http_handlers import HTTPRouteHandler

if TYPE_CHECKING:
    from litestar.openapi.spec.open_api import OpenAPI


@pytest.fixture()
def handler() -> HTTPRouteHandler:
    @get("/handler", tags=["handler"])
    def _handler() -> Any: ...

    return _handler


@pytest.fixture()
def controller() -> Type[Controller]:
    class _Controller(Controller):
        path = "/controller"
        tags = ["controller"]

        @get(tags=["handler", "a"])
        def _handler(self) -> Any: ...

    return _Controller


@pytest.fixture()
def router(controller: Type[Controller]) -> Router:
    return Router(path="/router", route_handlers=[controller], tags=["router"])


@pytest.fixture()
def app(handler: HTTPRouteHandler, controller: Type[Controller], router: Router) -> Litestar:
    return Litestar(route_handlers=[handler, controller, router])


@pytest.fixture()
def openapi_schema(app: Litestar) -> "OpenAPI":
    return app.openapi_schema


def test_openapi_schema_handler_tags(openapi_schema: "OpenAPI") -> None:
    assert openapi_schema.paths["/handler"].get.tags == ["handler"]  # type: ignore[index, union-attr]


def test_openapi_schema_controller_tags(openapi_schema: "OpenAPI") -> None:
    assert openapi_schema.paths["/controller"].get.tags == ["a", "controller", "handler"]  # type: ignore[index, union-attr]


def test_openapi_schema_router_tags(openapi_schema: "OpenAPI") -> None:
    assert openapi_schema.paths["/router/controller"].get.tags == ["a", "controller", "handler", "router"]  # type: ignore[index, union-attr]
