from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, cast

import pytest

from litestar import Controller, Litestar, Request, Router, get
from litestar._openapi.path_item import create_path_item
from litestar._openapi.utils import default_operation_id_creator
from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers.http_handlers import HTTPRouteHandler
from litestar.openapi.spec import Operation
from litestar.utils import find_index

if TYPE_CHECKING:
    from litestar.routes import HTTPRoute


@pytest.fixture()
def route(person_controller: Type[Controller]) -> "HTTPRoute":
    app = Litestar(route_handlers=[person_controller], openapi_config=None)
    index = find_index(app.routes, lambda x: x.path_format == "/{service_id}/person/{person_id}")
    return cast("HTTPRoute", app.routes[index])


@pytest.fixture()
def routes_with_router(person_controller: Type[Controller]) -> Tuple["HTTPRoute", "HTTPRoute"]:
    class PersonControllerV2(person_controller):  # type: ignore
        pass

    router_v1 = Router(path="/v1", route_handlers=[person_controller])
    router_v2 = Router(path="/v2", route_handlers=[PersonControllerV2])
    app = Litestar(route_handlers=[router_v1, router_v2], openapi_config=None)
    index_v1 = find_index(app.routes, lambda x: x.path_format == "/v1/{service_id}/person/{person_id}")
    index_v2 = find_index(app.routes, lambda x: x.path_format == "/v2/{service_id}/person/{person_id}")
    return cast("HTTPRoute", app.routes[index_v1]), cast("HTTPRoute", app.routes[index_v2])


def test_create_path_item(route: "HTTPRoute") -> None:
    schema, _ = create_path_item(
        route=route,
        create_examples=True,
        plugins=[],
        use_handler_docstrings=False,
        operation_id_creator=default_operation_id_creator,
        schemas={},
    )
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


def test_unique_operation_ids_for_multiple_http_methods() -> None:
    class MultipleMethodsRouteController(Controller):
        path = "/"

        @HTTPRouteHandler("/", http_method=["GET", "HEAD"])
        async def root(self, *, request: Request[str, str, Any]) -> None:
            pass

    app = Litestar(route_handlers=[MultipleMethodsRouteController], openapi_config=None)
    index = find_index(app.routes, lambda x: x.path_format == "/")
    route_with_multiple_methods = cast("HTTPRoute", app.routes[index])
    schema, _ = create_path_item(
        route=route_with_multiple_methods,
        create_examples=True,
        plugins=[],
        use_handler_docstrings=False,
        operation_id_creator=default_operation_id_creator,
        schemas={},
    )
    assert schema.get
    assert schema.get.operation_id
    assert schema.head
    assert schema.head.operation_id
    assert schema.get.operation_id != schema.head.operation_id


def test_unique_operation_ids_for_multiple_http_methods_with_handler_level_operation_creator() -> None:
    class MultipleMethodsRouteController(Controller):
        path = "/"

        @HTTPRouteHandler("/", http_method=["GET", "HEAD"], operation_id=default_operation_id_creator)
        async def root(self, *, request: Request[str, str, Any]) -> None:
            pass

    app = Litestar(route_handlers=[MultipleMethodsRouteController], openapi_config=None)
    index = find_index(app.routes, lambda x: x.path_format == "/")
    route_with_multiple_methods = cast("HTTPRoute", app.routes[index])
    schema, _ = create_path_item(
        route=route_with_multiple_methods,
        create_examples=True,
        plugins=[],
        use_handler_docstrings=False,
        operation_id_creator=lambda x: "abc",  # type: ignore
        schemas={},
    )
    assert schema.get
    assert schema.get.operation_id
    assert schema.head
    assert schema.head.operation_id
    assert schema.get.operation_id != schema.head.operation_id


def test_routes_with_different_paths_should_generate_unique_operation_ids(
    routes_with_router: Tuple["HTTPRoute", "HTTPRoute"]
) -> None:
    route_v1, route_v2 = routes_with_router
    schema_v1, _ = create_path_item(
        route=route_v1,
        create_examples=True,
        plugins=[],
        use_handler_docstrings=False,
        operation_id_creator=default_operation_id_creator,
        schemas={},
    )
    schema_v2, _ = create_path_item(
        route=route_v2,
        create_examples=True,
        plugins=[],
        use_handler_docstrings=False,
        operation_id_creator=default_operation_id_creator,
        schemas={},
    )
    assert schema_v1.get
    assert schema_v2.get
    assert schema_v1.get.operation_id != schema_v2.get.operation_id


def test_create_path_item_use_handler_docstring_false(route: "HTTPRoute") -> None:
    schema, _ = create_path_item(
        route=route,
        create_examples=True,
        plugins=[],
        use_handler_docstrings=False,
        operation_id_creator=default_operation_id_creator,
        schemas={},
    )
    assert schema.get
    assert schema.get.description is None
    assert schema.patch
    assert schema.patch.description == "Description in decorator"


def test_create_path_item_use_handler_docstring_true(route: "HTTPRoute") -> None:
    schema, _ = create_path_item(
        route=route,
        create_examples=True,
        plugins=[],
        use_handler_docstrings=True,
        operation_id_creator=default_operation_id_creator,
        schemas={},
    )
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
    def handler_1() -> None:
        ...

    @get(path="/2", operation_id="handler")
    def handler_2() -> None:
        ...

    app = Litestar(route_handlers=[handler_1, handler_2])

    with pytest.raises(ImproperlyConfiguredException):
        app.openapi_schema


def test_operation_override() -> None:
    @dataclass
    class CustomOperation(Operation):
        x_code_samples: Optional[List[Dict[str, str]]] = field(default=None, metadata={"alias": "x-codeSamples"})

        def __post_init__(self) -> None:
            self.tags = ["test"]
            self.description = "test"
            self.x_code_samples = [
                {"lang": "Python", "source": "import requests; requests.get('localhost/example')", "label": "Python"},
                {"lang": "cURL", "source": "curl -XGET localhost/example", "label": "curl"},
            ]

    @get(path="/1")
    def handler_1() -> None:
        ...

    @get(path="/2", operation_class=CustomOperation)
    def handler_2() -> None:
        ...

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

def test_operation_override_callable() -> None:
    @dataclass
    class CustomOperation(Operation):
        x_my_value: Optional[str] = field(default=None, metadata={"alias": "x-my-value"})
        x_default_value: Optional[str] = field(default=None, metadata={"alias": "x-default-value"})
        
        def __post_init__(self) -> None:
            self.tags = ["test"]
            self.x_my_value = "post_init_x_my_value"
            self.x_default_value = "post_init_x_default_value"


    def custom_operation_callable(operation: CustomOperation, route: HTTPRouteHandler):
        operation.x_my_value = "callable_set_x_my_value"
        operation.tags = ["callable_tag"]
        operation.description = route.opt.get("value_from_opts")
        

    @get(path="/1", operation_class=CustomOperation, operation_callable=custom_operation_callable, value_from_opts="value_from_opt")
    def handler_1() -> None:
        ...

    app = Litestar(route_handlers=[handler_1])

   
    assert app.openapi_schema.paths["/1"]
    assert app.openapi_schema.paths["/1"].get
    assert isinstance(app.openapi_schema.paths["/1"].get, CustomOperation)
    assert app.openapi_schema.paths["/1"].get.tags == ["callable_tag"]
    assert app.openapi_schema.paths["/1"].get.description == "value_from_opt"
    assert app.openapi_schema.paths["/1"].get.x_my_value == "callable_set_x_my_value"
    assert app.openapi_schema.paths["/1"].get.x_default_value == "post_init_x_default_value"

    operation_schema = CustomOperation().to_schema()
    assert "x-my-value" in operation_schema
    assert "x-default-value" in operation_schema
