from typing import List

import pytest

from litestar import Controller, Router, get
from litestar.params import Parameter
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client


def test_layered_parameters_injected_correctly() -> None:
    class MyController(Controller):
        path = "/controller"
        parameters = {"controller1": Parameter(lt=100), "controller2": Parameter(str, query="controller3")}

        @get("/{local:int}")
        def my_handler(
            self,
            local: float,
            controller1: int,
            controller2: str,
            router1: str,
            router2: float,
            app1: str,
            app2: List[str],
        ) -> dict:
            assert isinstance(local, float)
            assert isinstance(controller1, int)
            assert isinstance(controller2, str)
            assert isinstance(router1, str)
            assert isinstance(router2, float)
            assert isinstance(app1, str)
            assert isinstance(app2, list)
            return {"message": "ok"}

    router = Router(
        path="/router",
        route_handlers=[MyController],
        parameters={
            "router1": Parameter(str, pattern="^[a-zA-Z]$"),
            "router2": Parameter(float, multiple_of=5.0, header="router3"),
        },
    )

    with create_test_client(
        route_handlers=router,
        parameters={
            "app1": Parameter(str, cookie="app4"),
            "app2": Parameter(List[str], min_items=2),
            "app3": Parameter(bool, required=False),
        },
    ) as client:
        # Set cookies on the client to avoid warnings about per-request cookies.
        client.cookies = {"app4": "jeronimo"}  # type: ignore[assignment]

        query = {"controller1": "99", "controller3": "tuna", "router1": "albatross", "app2": ["x", "y"]}
        headers = {"router3": "10"}

        response = client.get("/router/controller/1", params=query, headers=headers)
        assert response.json() == {"message": "ok"}
        assert response.status_code == HTTP_200_OK


@pytest.mark.parametrize(
    "parameter,param_type",
    [
        ("controller1", "query"),
        ("controller3", "query"),
        ("router1", "query"),
        ("router3", "header"),
        ("app4", "cookie"),
        ("app2", "query"),
    ],
)
def test_layered_parameters_validation(parameter: str, param_type: str) -> None:
    class MyController(Controller):
        path = "/controller"
        parameters = {"controller1": Parameter(int, lt=100), "controller2": Parameter(str, query="controller3")}

        @get("/{local:int}")
        def my_handler(self) -> dict:
            return {}

    router = Router(
        path="/router",
        route_handlers=[MyController],
        parameters={
            "router1": Parameter(str, pattern="^[a-zA-Z]$"),
            "router2": Parameter(float, multiple_of=5.0, header="router3"),
        },
    )

    with create_test_client(
        route_handlers=router,
        parameters={
            "app1": Parameter(str, cookie="app4"),
            "app2": Parameter(List[str], min_items=2),
            "app3": Parameter(bool, required=False),
        },
    ) as client:
        query = {"controller1": "99", "controller3": "tuna", "router1": "albatross", "app2": ["x", "y"]}
        headers = {"router3": "10"}
        cookies = {"app4": "jeronimo"}

        if parameter in headers:
            headers = {}
        elif parameter in cookies:
            cookies = {}
        else:
            query.pop(parameter)

        # Set cookies on the client to avoid warnings about per-request cookies.
        client.cookies = cookies  # type: ignore[assignment]

        response = client.get("/router/controller/1", params=query, headers=headers)

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.json()["detail"].startswith(f"Missing required {param_type} parameter '{parameter}' for path")


def test_layered_parameters_defaults_and_overrides() -> None:
    class MyController(Controller):
        path = "/controller"
        parameters = {"controller1": Parameter(int, default=50), "controller2": Parameter(str, query="controller3")}

        @get("/{local:int}")
        def my_handler(
            self,
            local: float,
            controller1: int,
            controller2: str = Parameter(str, query="controller4"),
            app1: str = Parameter(default="moishe"),
        ) -> dict:
            assert app1 == "moishe"
            assert controller2 == "jeronimo"
            assert controller1 == 50
            return {"message": "ok"}

    router = Router(
        path="/router",
        route_handlers=[MyController],
    )

    with create_test_client(
        route_handlers=router,
        parameters={
            "app1": Parameter(str, default="haim"),
        },
    ) as client:
        query = {"controller4": "jeronimo"}

        response = client.get("/router/controller/1", params=query)
        assert response.json() == {"message": "ok"}
        assert response.status_code == HTTP_200_OK


def test_layered_include_in_schema_parameter() -> None:
    class IncludedAtController(Controller):
        path = "included_controller"
        include_in_schema = True

        @get("included_handler", include_in_schema=True)
        async def included_handler(self) -> None:
            # included at handler layer
            return None

        @get("excluded_handler", include_in_schema=False)
        async def excluded_handler(self) -> None:
            # excluded at handler layer
            return None

        @get("handler")
        async def route(self) -> None:
            # included at controller layer
            return None

    class ExlcudedAtController(Controller):
        path = "excluded_controller"
        include_in_schema = False

        @get("included_handler", include_in_schema=True)
        async def included_handler(self) -> None:
            # included at handler layer
            return None

        @get("excluded_handler", include_in_schema=False)
        async def excluded_handler(self) -> None:
            # excluded at handler layer
            return None

        @get("handler")
        async def route(self) -> None:
            # excluded at controller layer
            return None

    @get("included_handler", include_in_schema=True)
    async def included_handler() -> None:
        # included at handler layer
        return None

    @get("excluded_handler", include_in_schema=False)
    async def excluded_handler() -> None:
        # excluded at handler layer
        return None

    @get("handler")
    async def route() -> None:
        # included or excluded depending on
        # the app or router layer setting
        return None

    common_routes = [included_handler, excluded_handler, route]
    IncludedAtRouter = Router(
        "included_router",
        route_handlers=common_routes,
        include_in_schema=True,
    )
    ExlcudedAtRouter = Router(
        "excluded_router",
        route_handlers=common_routes,
        include_in_schema=False,
    )

    with create_test_client(
        [IncludedAtController, ExlcudedAtController, IncludedAtRouter, ExlcudedAtRouter, *common_routes],
        include_in_schema=False,
    ) as client:
        app = client.app
        assert app.openapi_schema.paths

        # routes that must be included
        assert "/included_controller/included_handler" in app.openapi_schema.paths
        assert "/included_controller/handler" in app.openapi_schema.paths
        assert "/excluded_controller/included_handler" in app.openapi_schema.paths
        assert "/included_router/included_handler" in app.openapi_schema.paths
        assert "/included_router/handler" in app.openapi_schema.paths
        assert "/excluded_router/included_handler" in app.openapi_schema.paths
        assert "/included_handler" in app.openapi_schema.paths

        # routes that must be excluded
        assert "/included_controller/excluded_handler" not in app.openapi_schema.paths
        assert "/excluded_controller/handler" not in app.openapi_schema.paths
        assert "/excluded_controller/excluded_handler" not in app.openapi_schema.paths
        assert "/included_router/excluded_handler" not in app.openapi_schema.paths
        assert "/excluded_router/handler" not in app.openapi_schema.paths
        assert "/excluded_router/excluded_handler" not in app.openapi_schema.paths
        assert "/excluded_handler" not in app.openapi_schema.paths
        assert "/handler" not in app.openapi_schema.paths
