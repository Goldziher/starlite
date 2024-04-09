from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, cast
from unittest.mock import MagicMock

import pytest
from typing_extensions import TypeAlias

from litestar import Controller, HttpMethod, Litestar, Request, Router, delete, get
from litestar._openapi.datastructures import OpenAPIContext
from litestar._openapi.path_item import PathItemFactory, merge_path_item_operations
from litestar._openapi.utils import default_operation_id_creator
from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers.http_handlers import HTTPRouteHandler
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Operation, PathItem
from litestar.utils import find_index

if TYPE_CHECKING:
    from litestar.routes import HTTPRoute


@pytest.fixture()
def route(person_controller: type[Controller]) -> HTTPRoute:
    app = Litestar(route_handlers=[person_controller], openapi_config=None)
    index = find_index(app.routes, lambda x: x.path_format == "/{service_id}/person/{person_id}")
    return cast("HTTPRoute", app.routes[index])


@pytest.fixture()
def routes_with_router(person_controller: type[Controller]) -> tuple[HTTPRoute, HTTPRoute]:
    class PersonControllerV2(person_controller):  # type: ignore[misc, valid-type]
        pass

    router_v1 = Router(path="/v1", route_handlers=[person_controller])
    router_v2 = Router(path="/v2", route_handlers=[PersonControllerV2])
    app = Litestar(route_handlers=[router_v1, router_v2], openapi_config=None)
    index_v1 = find_index(app.routes, lambda x: x.path_format == "/v1/{service_id}/person/{person_id}")
    index_v2 = find_index(app.routes, lambda x: x.path_format == "/v2/{service_id}/person/{person_id}")
    return cast("HTTPRoute", app.routes[index_v1]), cast("HTTPRoute", app.routes[index_v2])


CreateFactoryFixture: TypeAlias = "Callable[[HTTPRoute], PathItemFactory]"


@pytest.fixture()
def create_factory() -> CreateFactoryFixture:
    def factory(route: HTTPRoute) -> PathItemFactory:
        return PathItemFactory(
            OpenAPIContext(
                openapi_config=OpenAPIConfig(title="Test", version="1.0.0", description="Test", create_examples=True),
                plugins=[],
            ),
            route,
        )

    return factory


def test_create_path_item(route: HTTPRoute, create_factory: CreateFactoryFixture) -> None:
    schema = create_factory(route).create_path_item()
    assert schema.delete
    assert schema.delete.operation_id == "ServiceIdPersonPersonIdDeletePerson"
    assert schema.delete.summary == "DeletePerson"
    assert schema.get
    assert schema.get.operation_id == "ServiceIdPersonPersonIdGetPersonById"
    assert schema.get.summary == "GetPersonById"
    assert schema.patch
    assert schema.patch.operation_id == "ServiceIdPersonPersonIdPartialUpdatePerson"
    assert schema.patch.summary == "PartialUpdatePerson"
    assert schema.put
    assert schema.put.operation_id == "ServiceIdPersonPersonIdUpdatePerson"
    assert schema.put.summary == "UpdatePerson"


def test_unique_operation_ids_for_multiple_http_methods(create_factory: CreateFactoryFixture) -> None:
    class MultipleMethodsRouteController(Controller):
        path = "/"

        @HTTPRouteHandler("/", http_method=["GET", "HEAD"])
        async def root(self, *, request: Request[str, str, Any]) -> None:
            pass

    app = Litestar(route_handlers=[MultipleMethodsRouteController], openapi_config=None)
    index = find_index(app.routes, lambda x: x.path_format == "/")
    route_with_multiple_methods = cast("HTTPRoute", app.routes[index])
    schema = create_factory(route_with_multiple_methods).create_path_item()
    assert schema.get
    assert schema.get.operation_id
    assert schema.head
    assert schema.head.operation_id
    assert schema.get.operation_id != schema.head.operation_id


def test_unique_operation_ids_for_multiple_http_methods_with_handler_level_operation_creator(
    create_factory: CreateFactoryFixture,
) -> None:
    class MultipleMethodsRouteController(Controller):
        path = "/"

        @HTTPRouteHandler("/", http_method=["GET", "HEAD"], operation_id=default_operation_id_creator)
        async def root(self, *, request: Request[str, str, Any]) -> None:
            pass

    app = Litestar(route_handlers=[MultipleMethodsRouteController], openapi_config=None)
    index = find_index(app.routes, lambda x: x.path_format == "/")
    route_with_multiple_methods = cast("HTTPRoute", app.routes[index])
    factory = create_factory(route_with_multiple_methods)
    factory.context.openapi_config.operation_id_creator = lambda x: "abc"  # type: ignore[assignment, misc]
    schema = create_factory(route_with_multiple_methods).create_path_item()
    assert schema.get
    assert schema.get.operation_id
    assert schema.head
    assert schema.head.operation_id
    assert schema.get.operation_id != schema.head.operation_id


def test_routes_with_different_paths_should_generate_unique_operation_ids(
    routes_with_router: tuple[HTTPRoute, HTTPRoute], create_factory: CreateFactoryFixture
) -> None:
    route_v1, route_v2 = routes_with_router
    schema_v1 = create_factory(route_v1).create_path_item()
    schema_v2 = create_factory(route_v2).create_path_item()
    assert schema_v1.get
    assert schema_v2.get
    assert schema_v1.get.operation_id != schema_v2.get.operation_id


def test_create_path_item_use_handler_docstring_false(route: HTTPRoute, create_factory: CreateFactoryFixture) -> None:
    factory = create_factory(route)
    assert not factory.context.openapi_config.use_handler_docstrings
    schema = factory.create_path_item()
    assert schema.get
    assert schema.get.description is None
    assert schema.patch
    assert schema.patch.description == "Description in decorator"


def test_create_path_item_use_handler_docstring_true(route: HTTPRoute, create_factory: CreateFactoryFixture) -> None:
    factory = create_factory(route)
    factory.context.openapi_config.use_handler_docstrings = True
    schema = factory.create_path_item()
    assert schema.get
    assert schema.get.description == "Description in docstring."
    assert schema.patch
    assert schema.patch.description == "Description in decorator"
    assert schema.put
    assert schema.put.description
    # make sure multiline docstring is fully included
    assert "Line 3." in schema.put.description
    # make sure internal docstring indentation used to line up with the code
    # is removed from description
    assert "    " not in schema.put.description


def test_operation_id_validation() -> None:
    @get(path="/1", operation_id="handler")
    def handler_1() -> None: ...

    @get(path="/2", operation_id="handler")
    def handler_2() -> None: ...

    app = Litestar(route_handlers=[handler_1, handler_2])

    with pytest.raises(ImproperlyConfiguredException):
        app.openapi_schema


def test_operation_override() -> None:
    @dataclass
    class CustomOperation(Operation):
        x_code_samples: list[dict[str, str]] | None = field(default=None, metadata={"alias": "x-codeSamples"})

        def __post_init__(self) -> None:
            self.tags = ["test"]
            self.description = "test"
            self.x_code_samples = [
                {"lang": "Python", "source": "import requests; requests.get('localhost/example')", "label": "Python"},
                {"lang": "cURL", "source": "curl -XGET localhost/example", "label": "curl"},
            ]

    @get(path="/1")
    def handler_1() -> None: ...

    @get(path="/2", operation_class=CustomOperation)
    def handler_2() -> None: ...

    app = Litestar(route_handlers=[handler_1, handler_2])

    assert app.openapi_schema.paths
    assert app.openapi_schema.paths["/1"]
    assert app.openapi_schema.paths["/1"].get
    assert isinstance(app.openapi_schema.paths["/1"].get, Operation)
    assert app.openapi_schema.paths["/2"]
    assert app.openapi_schema.paths["/2"].get
    assert isinstance(app.openapi_schema.paths["/2"].get, CustomOperation)
    assert app.openapi_schema.paths["/2"].get.tags == ["test"]
    assert app.openapi_schema.paths["/2"].get.description == "test"

    operation_schema = CustomOperation().to_schema()
    assert "x-codeSamples" in operation_schema


def test_handler_excluded_from_schema(create_factory: CreateFactoryFixture) -> None:
    @get("/", sync_to_thread=False)
    def handler_1() -> None: ...

    @delete("/", include_in_schema=False, sync_to_thread=False)
    def handler_2() -> None: ...

    app = Litestar(route_handlers=[handler_1, handler_2])
    index = find_index(app.routes, lambda x: x.path_format == "/")
    route_with_multiple_methods = cast("HTTPRoute", app.routes[index])
    factory = create_factory(route_with_multiple_methods)
    schema = factory.create_path_item()
    assert schema.get
    assert schema.delete is None


@pytest.mark.parametrize("method", HttpMethod)
def test_merge_path_item_operations_operation_set_on_both_raises(method: HttpMethod) -> None:
    with pytest.raises(ValueError, match="Cannot merge operation"):
        merge_path_item_operations(
            PathItem(**{method.value.lower(): MagicMock()}),
            PathItem(**{method.value.lower(): MagicMock()}),
            for_path="/",
        )


@pytest.mark.parametrize(
    "attr",
    [
        f.name
        for f in dataclasses.fields(PathItem)
        if f.name.upper()
        not in [
            *HttpMethod,
            "TRACE",  # remove once https://github.com/litestar-org/litestar/pull/3294 is merged
        ]
    ],
)
def test_merge_path_item_operation_differing_values_raises(attr: str) -> None:
    with pytest.raises(ImproperlyConfiguredException, match="Conflicting OpenAPI path configuration for '/'"):
        merge_path_item_operations(PathItem(), PathItem(**{attr: MagicMock()}), for_path="/")
