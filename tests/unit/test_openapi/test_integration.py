from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Generic, Optional, TypeVar, cast

import msgspec
import pytest
import yaml
from typing_extensions import Annotated

from litestar import Controller, Litestar, Router, delete, get, patch, post
from litestar._openapi.plugin import OpenAPIPlugin
from litestar.enums import MediaType, OpenAPIMediaType, ParamType
from litestar.openapi import OpenAPIConfig, OpenAPIController
from litestar.openapi.spec import Parameter as OpenAPIParameter
from litestar.params import Parameter
from litestar.serialization.msgspec_hooks import decode_json, encode_json, get_serializer
from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from litestar.testing import create_test_client

CREATE_EXAMPLES_VALUES = (True, False)


@pytest.fixture(params=[True, False])
def create_examples(request: pytest.FixtureRequest) -> bool:
    return request.param  # type: ignore[no-any-return]


@pytest.mark.parametrize("schema_path", ["/schema/openapi.yaml", "/schema/openapi.yml"])
def test_openapi(
    person_controller: type[Controller],
    pet_controller: type[Controller],
    create_examples: bool,
    schema_path: str,
    openapi_controller: type[OpenAPIController] | None,
) -> None:
    openapi_config = OpenAPIConfig(
        "Example API", "1.0.0", create_examples=create_examples, openapi_controller=openapi_controller
    )
    with create_test_client([person_controller, pet_controller], openapi_config=openapi_config) as client:
        assert client.app.openapi_schema
        openapi_schema = client.app.openapi_schema
        assert openapi_schema.paths
        response = client.get(schema_path)
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"] == OpenAPIMediaType.OPENAPI_YAML.value
        assert client.app.openapi_schema
        serializer = get_serializer(client.app.type_encoders)
        schema_json = decode_json(encode_json(openapi_schema.to_schema(), serializer))
        assert response.content.decode("utf-8") == yaml.dump(schema_json)


def test_openapi_json(
    person_controller: type[Controller],
    pet_controller: type[Controller],
    create_examples: bool,
    openapi_controller: type[OpenAPIController] | None,
) -> None:
    openapi_config = OpenAPIConfig(
        "Example API", "1.0.0", create_examples=create_examples, openapi_controller=openapi_controller
    )
    with create_test_client([person_controller, pet_controller], openapi_config=openapi_config) as client:
        assert client.app.openapi_schema
        openapi_schema = client.app.openapi_schema
        assert openapi_schema.paths
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"] == OpenAPIMediaType.OPENAPI_JSON.value
        assert client.app.openapi_schema
        serializer = get_serializer(client.app.type_encoders)
        assert response.content == encode_json(openapi_schema.to_schema(), serializer)


@pytest.mark.parametrize(
    "endpoint, schema_path", [("openapi.yaml", "/schema/openapi.yaml"), ("openapi.yml", "/schema/openapi.yml")]
)
def test_openapi_yaml_not_allowed(
    endpoint: str,
    schema_path: str,
    person_controller: type[Controller],
    pet_controller: type[Controller],
    openapi_controller: type[OpenAPIController] | None,
) -> None:
    openapi_config = OpenAPIConfig(
        "Example API", "1.0.0", enabled_endpoints=set(), openapi_controller=openapi_controller
    )

    with create_test_client([person_controller, pet_controller], openapi_config=openapi_config) as client:
        assert client.app.openapi_schema
        openapi_schema = client.app.openapi_schema
        assert openapi_schema.paths
        response = client.get(schema_path)
        assert response.status_code == HTTP_404_NOT_FOUND


def test_openapi_json_not_allowed(person_controller: type[Controller], pet_controller: type[Controller]) -> None:
    # only tested with the OpenAPIController, b/c new router based approach always serves `openapi.json`.
    openapi_config = OpenAPIConfig(
        "Example API",
        "1.0.0",
        enabled_endpoints=set(),
        openapi_controller=OpenAPIController,
    )

    with create_test_client([person_controller, pet_controller], openapi_config=openapi_config) as client:
        assert client.app.openapi_schema
        openapi_schema = client.app.openapi_schema
        assert openapi_schema.paths
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_404_NOT_FOUND


def test_openapi_custom_path(openapi_controller: type[OpenAPIController] | None) -> None:
    openapi_config = OpenAPIConfig(
        title="my title", version="1.0.0", path="/custom_schema_path", openapi_controller=openapi_controller
    )
    with create_test_client([], openapi_config=openapi_config) as client:
        response = client.get("/schema")
        assert response.status_code == HTTP_404_NOT_FOUND

        response = client.get("/custom_schema_path")
        assert response.status_code == HTTP_200_OK

        response = client.get("/custom_schema_path/openapi.json")
        assert response.status_code == HTTP_200_OK


def test_openapi_normalizes_custom_path(openapi_controller: type[OpenAPIController] | None) -> None:
    openapi_config = OpenAPIConfig(
        title="my title", version="1.0.0", path="custom_schema_path", openapi_controller=openapi_controller
    )
    with create_test_client([], openapi_config=openapi_config) as client:
        response = client.get("/custom_schema_path/openapi.json")
        assert response.status_code == HTTP_200_OK

        response = client.get("/custom_schema_path/openapi.json")
        assert response.status_code == HTTP_200_OK


def test_openapi_custom_path_avoids_override() -> None:
    class CustomOpenAPIController(OpenAPIController):
        path = "/custom_docs"

    openapi_config = OpenAPIConfig(title="my title", version="1.0.0", openapi_controller=CustomOpenAPIController)
    with create_test_client([], openapi_config=openapi_config) as client:
        response = client.get("/schema")
        assert response.status_code == HTTP_404_NOT_FOUND

        response = client.get("/custom_docs/openapi.json")
        assert response.status_code == HTTP_200_OK

        response = client.get("/custom_docs/openapi.json")
        assert response.status_code == HTTP_200_OK


def test_openapi_custom_path_overrides_custom_controller_path() -> None:
    class CustomOpenAPIController(OpenAPIController):
        path = "/custom_docs"

    openapi_config = OpenAPIConfig(
        title="my title", version="1.0.0", openapi_controller=CustomOpenAPIController, path="/override_docs_path"
    )
    with create_test_client([], openapi_config=openapi_config) as client:
        response = client.get("/custom_docs")
        assert response.status_code == HTTP_404_NOT_FOUND

        response = client.get("/override_docs_path/openapi.json")
        assert response.status_code == HTTP_200_OK

        response = client.get("/override_docs_path/openapi.json")
        assert response.status_code == HTTP_200_OK


def test_msgspec_schema_generation(create_examples: bool, openapi_controller: type[OpenAPIController] | None) -> None:
    class Lookup(msgspec.Struct):
        id: Annotated[
            str,
            msgspec.Meta(
                min_length=12,
                max_length=16,
                description="A unique identifier",
                examples=["e4eaaaf2-d142-11e1-b3e4-080027620cdd"],
            ),
        ]

    @post("/example")
    async def example_route() -> Lookup:
        return Lookup(id="1234567812345678")

    with create_test_client(
        route_handlers=[example_route],
        openapi_config=OpenAPIConfig(
            title="Example API",
            version="1.0.0",
            create_examples=create_examples,
            openapi_controller=openapi_controller,
        ),
        signature_types=[Lookup],
    ) as client:
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_200_OK
        assert response.json()["components"]["schemas"]["test_msgspec_schema_generation.Lookup"]["properties"][
            "id"
        ] == {
            "description": "A unique identifier",
            "examples": ["e4eaaaf2-d142-11e1-b3e4-080027620cdd"],
            "maxLength": 16,
            "minLength": 12,
            "type": "string",
        }


def test_dataclass_field_default() -> None:
    # https://github.com/litestar-org/litestar/issues/3201
    @dataclass
    class SomeModel:
        field_a: str = "default_a"
        field_b: str = dataclasses.field(default="default_b")
        field_c: str = dataclasses.field(default_factory=lambda: "default_c")

    @get("/")
    async def handler() -> SomeModel:
        return SomeModel()

    app = Litestar(route_handlers=[handler], signature_types=[SomeModel])
    schema = app.openapi_schema.components.schemas["test_dataclass_field_default.SomeModel"]
    assert schema
    assert schema.properties["field_a"].default == "default_a"  # type: ignore[union-attr, index]
    assert schema.properties["field_b"].default == "default_b"  # type: ignore[union-attr, index]
    assert schema.properties["field_c"].default is None  # type: ignore[union-attr, index]


def test_struct_field_default() -> None:
    # https://github.com/litestar-org/litestar/issues/3201
    class SomeModel(msgspec.Struct, kw_only=True):
        field_a: str = "default_a"
        field_b: str = msgspec.field(default="default_b")
        field_c: str = msgspec.field(default_factory=lambda: "default_c")

    @get("/")
    async def handler() -> SomeModel:
        return SomeModel()

    app = Litestar(route_handlers=[handler], signature_types=[SomeModel])
    schema = app.openapi_schema.components.schemas["test_struct_field_default.SomeModel"]
    assert schema
    assert schema.properties["field_a"].default == "default_a"  # type: ignore[union-attr, index]
    assert schema.properties["field_b"].default == "default_b"  # type: ignore[union-attr, index]
    assert schema.properties["field_c"].default is None  # type: ignore[union-attr, index]


def test_schema_for_optional_path_parameter(openapi_controller: type[OpenAPIController] | None) -> None:
    @get(path=["/", "/{test_message:str}"], media_type=MediaType.TEXT, sync_to_thread=False)
    def handler(test_message: Optional[str]) -> str:  # noqa: UP007
        return test_message or "no message"

    with create_test_client(
        route_handlers=[handler],
        openapi_config=OpenAPIConfig(
            title="Example API",
            version="1.0.0",
            create_examples=True,
            openapi_controller=openapi_controller,
        ),
    ) as client:
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_200_OK
        assert "parameters" not in response.json()["paths"]["/"]["get"]  # type[ignore]
        parameter = response.json()["paths"]["/{test_message}"]["get"]["parameters"][0]  # type[ignore]
        assert parameter
        assert parameter["in"] == ParamType.PATH
        assert parameter["name"] == "test_message"


T = TypeVar("T")


@dataclass
class Foo(Generic[T]):
    foo: T


def test_with_generic_class(openapi_controller: type[OpenAPIController] | None) -> None:
    @get("/foo-str", sync_to_thread=False)
    def handler_foo_str() -> Foo[str]:
        return Foo("")

    @get("/foo-int", sync_to_thread=False)
    def handler_foo_int() -> Foo[int]:
        return Foo(1)

    with create_test_client(
        route_handlers=[handler_foo_str, handler_foo_int],
        openapi_config=OpenAPIConfig(
            title="Example API",
            version="1.0.0",
            openapi_controller=openapi_controller,
        ),
    ) as client:
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {
            "info": {"title": "Example API", "version": "1.0.0"},
            "openapi": "3.1.0",
            "servers": [{"url": "/"}],
            "paths": {
                "/foo-str": {
                    "get": {
                        "summary": "HandlerFooStr",
                        "operationId": "FooStrHandlerFooStr",
                        "responses": {
                            "200": {
                                "description": "Request fulfilled, document follows",
                                "headers": {},
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Foo[str]"}}},
                            }
                        },
                        "deprecated": False,
                    }
                },
                "/foo-int": {
                    "get": {
                        "summary": "HandlerFooInt",
                        "operationId": "FooIntHandlerFooInt",
                        "responses": {
                            "200": {
                                "description": "Request fulfilled, document follows",
                                "headers": {},
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Foo[int]"}}},
                            }
                        },
                        "deprecated": False,
                    }
                },
            },
            "components": {
                "schemas": {
                    "Foo[str]": {
                        "properties": {"foo": {"type": "string"}},
                        "type": "object",
                        "required": ["foo"],
                        "title": "Foo[str]",
                    },
                    "Foo[int]": {
                        "properties": {"foo": {"type": "integer"}},
                        "type": "object",
                        "required": ["foo"],
                        "title": "Foo[int]",
                    },
                }
            },
        }


def test_allow_multiple_parameters_with_same_name_but_different_location() -> None:
    """Test that we can support params with the same name if they are in different locations, e.g., cookie and header.

    https://github.com/litestar-org/litestar/issues/2662
    """

    @post("/test")
    async def route(
        name: Annotated[Optional[str], Parameter(cookie="name")] = None,  # noqa: UP007
        name_header: Annotated[Optional[str], Parameter(header="name")] = None,  # noqa: UP007
    ) -> str:
        return name or name_header or ""

    app = Litestar(route_handlers=[route], debug=True)
    assert app.openapi_schema.paths is not None
    schema = app.openapi_schema
    paths = schema.paths
    assert paths is not None
    path = paths["/test"]
    assert path.post is not None
    parameters = path.post.parameters
    assert parameters is not None
    assert len(parameters) == 2
    assert all(isinstance(param, OpenAPIParameter) for param in parameters)
    params = cast("list[OpenAPIParameter]", parameters)
    assert all(param.name == "name" for param in params)
    assert tuple(param.param_in for param in params) == ("cookie", "header")


def test_schema_name_collisions(create_module: Callable[[str], ModuleType]) -> None:
    module_a = create_module(
        """
from dataclasses import dataclass

@dataclass
class Model:
    a: str

"""
    )

    module_b = create_module(
        """
from dataclasses import dataclass

@dataclass
class Model:
    b: str

"""
    )

    @get("/foo", sync_to_thread=False, signature_namespace={"module_a": module_a})
    def handler_a() -> module_a.Model:  # type: ignore[name-defined]
        return module_a.Model(a="")

    @get("/bar", sync_to_thread=False, signature_namespace={"module_b": module_b})
    def handler_b() -> module_b.Model:  # type: ignore[name-defined]
        return module_b.Model(b="")

    app = Litestar(route_handlers=[handler_a, handler_b], debug=True)
    openapi_plugin = app.plugins.get(OpenAPIPlugin)
    assert openapi_plugin.provide_openapi().components.schemas.keys() == {
        f"{module_a.__name__}_Model",
        f"{module_b.__name__}_Model",
    }
    # TODO: expand this test to cover more cases


def test_multiple_handlers_for_same_route() -> None:
    @post("/", sync_to_thread=False)
    def post_handler() -> None: ...

    @get("/", sync_to_thread=False)
    def get_handler() -> None: ...

    app = Litestar([get_handler, post_handler])
    openapi_plugin = app.plugins.get(OpenAPIPlugin)
    openapi = openapi_plugin.provide_openapi()

    assert openapi.paths is not None
    path_item = openapi.paths["/"]
    assert path_item.get is not None
    assert path_item.post is not None


@pytest.mark.parametrize(("random_seed_one", "random_seed_two", "should_be_equal"), [(10, 10, True), (10, 20, False)])
def test_seeding(random_seed_one: int, random_seed_two: int, should_be_equal: bool) -> None:
    @post("/", sync_to_thread=False)
    def post_handler(q: str) -> None: ...

    @get("/", sync_to_thread=False)
    def get_handler(q: str) -> None: ...

    app = Litestar(
        [get_handler, post_handler], openapi_config=OpenAPIConfig("Litestar", "v0.0.1", True, random_seed_one)
    )
    openapi_plugin = app.plugins.get(OpenAPIPlugin)
    openapi_one = openapi_plugin.provide_openapi()

    app = Litestar(
        [get_handler, post_handler], openapi_config=OpenAPIConfig("Litestar", "v0.0.1", True, random_seed_two)
    )
    openapi_plugin = app.plugins.get(OpenAPIPlugin)
    openapi_two = openapi_plugin.provide_openapi()

    if should_be_equal:
        assert openapi_one == openapi_two
    else:
        assert openapi_one != openapi_two


def test_components_schemas_in_alphabetical_order() -> None:
    # https://github.com/litestar-org/litestar/issues/3059

    @dataclass
    class A: ...

    @dataclass
    class B: ...

    @dataclass
    class C: ...

    class TestController(Controller):
        @post("/", sync_to_thread=False)
        def post_handler(self, data: B) -> None: ...

        @get("/", sync_to_thread=False)
        def get_handler(self) -> A:  # type: ignore[empty-body]
            ...

        @patch("/", sync_to_thread=False)
        def patch_handler(self, data: C) -> A:  # type: ignore[empty-body]
            ...

        @delete("/", sync_to_thread=False)
        def delete_handler(self, data: B) -> None: ...

    app = Litestar([TestController], signature_types=[A, B, C])
    openapi_plugin = app.plugins.get(OpenAPIPlugin)
    openapi = openapi_plugin.provide_openapi()

    expected_keys = [
        "test_components_schemas_in_alphabetical_order.A",
        "test_components_schemas_in_alphabetical_order.B",
        "test_components_schemas_in_alphabetical_order.C",
    ]
    assert list(openapi.components.schemas.keys()) == expected_keys


def test_openapi_controller_and_openapi_router_on_same_app() -> None:
    """Test that OpenAPIController and OpenAPIRouter can coexist on the same app.

    As part of backward compatibility with new plugin-based OpenAPI router approach, we did not consider
    the case where an OpenAPIController is registered on the application by means other than via the
    OpenAPIConfig object. This is an approach that has been used to serve the openapi both under the
    `/schema` and `/some-prefix/schema` paths. This test ensures that the OpenAPIController and OpenAPIRouter
    can coexist on the same app.

    See: https://github.com/litestar-org/litestar/issues/3337
    """
    router = Router(path="/abc", route_handlers=[OpenAPIController])
    openapi_config = OpenAPIConfig("Litestar", "v0.0.1")  # no openapi_controller specified means we use the router
    app = Litestar([router], openapi_config=openapi_config)
    assert sorted(r.path for r in app.routes) == [
        "/abc/schema",
        "/abc/schema/elements",
        "/abc/schema/oauth2-redirect.html",
        "/abc/schema/openapi.json",
        "/abc/schema/openapi.yaml",
        "/abc/schema/openapi.yml",
        "/abc/schema/rapidoc",
        "/abc/schema/redoc",
        "/abc/schema/swagger",
        "/schema",
        "/schema/elements",
        "/schema/oauth2-redirect.html",
        "/schema/openapi.json",
        "/schema/openapi.yaml",
        "/schema/openapi.yml",
        "/schema/rapidoc",
        "/schema/redoc",
        "/schema/swagger",
        "/schema/{path:str}",
    ]
