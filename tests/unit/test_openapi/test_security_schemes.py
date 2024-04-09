from typing import TYPE_CHECKING, Any

import pytest

from litestar import Controller, Litestar, Router, get
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Components
from litestar.openapi.spec.security_scheme import SecurityScheme

if TYPE_CHECKING:
    from litestar.handlers.http_handlers import HTTPRouteHandler


@pytest.fixture()
def public_route() -> "HTTPRouteHandler":
    @get("/handler")
    def _handler() -> Any: ...

    return _handler


@pytest.fixture()
def protected_route() -> "HTTPRouteHandler":
    @get("/protected", security=[{"BearerToken": []}])
    def _handler() -> Any: ...

    return _handler


def test_schema_without_security_property(public_route: "HTTPRouteHandler") -> None:
    app = Litestar(route_handlers=[public_route])
    schema = app.openapi_schema

    assert schema
    assert schema.components
    assert not schema.components.security_schemes


def test_schema_with_security_scheme_defined(public_route: "HTTPRouteHandler") -> None:
    app = Litestar(
        route_handlers=[public_route],
        openapi_config=OpenAPIConfig(
            title="test app",
            version="0.0.1",
            components=Components(
                security_schemes={
                    "BearerToken": SecurityScheme(
                        type="http",
                        scheme="bearer",
                    )
                },
            ),
            security=[{"BearerToken": []}],
        ),
    )
    schema = app.openapi_schema
    assert schema
    schema_dict = schema.to_schema()

    schema_components = schema_dict.get("components", {})
    assert "securitySchemes" in schema_components

    assert schema_components.get("securitySchemes", {}) == {
        "BearerToken": {
            "type": "http",
            "scheme": "bearer",
        }
    }

    assert schema_dict.get("security", []) == [{"BearerToken": []}]


def test_schema_with_route_security_overridden(protected_route: "HTTPRouteHandler") -> None:
    app = Litestar(
        route_handlers=[protected_route],
        openapi_config=OpenAPIConfig(
            title="test app",
            version="0.0.1",
            components=Components(
                security_schemes={
                    "BearerToken": SecurityScheme(
                        type="http",
                        scheme="bearer",
                    )
                },
            ),
        ),
    )
    schema = app.openapi_schema
    assert schema
    schema_dict = schema.to_schema()

    route = schema_dict["paths"]["/protected"]["get"]
    assert route.get("security", None) == [{"BearerToken": []}]


def test_layered_security_declaration() -> None:
    class MyController(Controller):
        path = "/controller"
        security = [{"controllerToken": []}]  # pyright: ignore

        @get("", security=[{"handlerToken": []}])
        def my_handler(self) -> None: ...

    router = Router("/router", route_handlers=[MyController], security=[{"routerToken": []}])

    app = Litestar(
        route_handlers=[router],
        security=[{"appToken": []}],
        openapi_config=OpenAPIConfig(
            title="test app",
            version="0.0.1",
            components=Components(
                security_schemes={
                    "handlerToken": SecurityScheme(
                        type="http",
                        scheme="bearer",
                    ),
                    "controllerToken": SecurityScheme(
                        type="http",
                        scheme="bearer",
                    ),
                    "routerToken": SecurityScheme(
                        type="http",
                        scheme="bearer",
                    ),
                    "appToken": SecurityScheme(
                        type="http",
                        scheme="bearer",
                    ),
                },
            ),
        ),
    )
    assert app.openapi_schema
    assert app.openapi_schema.components
    security_schemes = app.openapi_schema.components.security_schemes
    assert security_schemes

    assert list(security_schemes.keys()) == [
        "handlerToken",
        "controllerToken",
        "routerToken",
        "appToken",
    ]

    assert app.openapi_schema
    paths = app.openapi_schema.paths
    assert paths
    assert paths["/router/controller"].get
    assert paths["/router/controller"].get.security == [
        {"appToken": []},
        {"routerToken": []},
        {"controllerToken": []},
        {"handlerToken": []},
    ]
