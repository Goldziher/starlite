import sys
from types import ModuleType
from typing import Any, Callable

import pytest
from msgspec import Struct

from litestar import delete, post
from litestar.openapi import ResponseSpec
from litestar.openapi.spec import OpenAPI
from litestar.status_codes import HTTP_204_NO_CONTENT
from litestar.testing import create_test_client
from tests.models import DataclassPerson, MsgSpecStructPerson, TypedDictPerson


@pytest.mark.parametrize("cls", (DataclassPerson, TypedDictPerson, MsgSpecStructPerson))
def test_spec_generation(cls: Any) -> None:
    @post("/")
    def handler(data: cls) -> cls:
        return data

    with create_test_client(handler) as client:
        schema = client.app.openapi_schema
        assert schema
        assert schema.to_schema()["components"]["schemas"][cls.__name__] == {
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "id": {"type": "string"},
                "optional": {"oneOf": [{"type": "null"}, {"type": "string"}]},
                "complex": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": {"type": "string"}},
                    },
                },
                "pets": {
                    "oneOf": [
                        {"type": "null"},
                        {
                            "items": {"$ref": "#/components/schemas/DataclassPet"},
                            "type": "array",
                        },
                    ]
                },
            },
            "type": "object",
            "required": ["complex", "first_name", "id", "last_name"],
            "title": f"{cls.__name__}",
        }


def test_spec_generation_no_content() -> None:
    @delete(
        "/",
        status_code=HTTP_204_NO_CONTENT,
        responses={204: ResponseSpec(None, description="Custom response")},
    )
    def handler() -> None:
        return None

    with create_test_client(handler) as client:
        schema: OpenAPI = client.app.openapi_schema
        assert schema.to_schema()["paths"] == {
            "/": {
                "delete": {
                    "summary": "Handler",
                    "deprecated": False,
                    "operationId": "Handler",
                    "responses": {
                        "204": {
                            "description": "Custom response",
                        }
                    },
                },
            },
        }


def test_msgspec_schema() -> None:
    class CamelizedStruct(Struct, rename="camel"):
        field_one: int
        field_two: float

    @post("/")
    def handler(data: CamelizedStruct) -> CamelizedStruct:
        return data

    with create_test_client(handler) as client:
        schema = client.app.openapi_schema
        assert schema

        assert schema.to_schema()["components"]["schemas"]["test_msgspec_schema.CamelizedStruct"] == {
            "properties": {"fieldOne": {"type": "integer"}, "fieldTwo": {"type": "number"}},
            "required": ["fieldOne", "fieldTwo"],
            "title": "CamelizedStruct",
            "type": "object",
        }


@pytest.fixture()
def py_38_module_content() -> str:
    return """
from __future__ import annotations

from typing import List, Optional

from msgspec import Struct

from litestar import Litestar, get

class A(Struct):
    a: A
    b: B
    opt_a: Optional[A] = None
    opt_b: Optional[B] = None
    list_a: List[A] = []
    list_b: List[B] = []

class B(Struct):
    a: A
    b: B
    opt_a: Optional[A] = None
    opt_b: Optional[B] = None
    list_a: List[A] = []
    list_b: List[B] = []

@get("/")
async def test() -> A:
    return A()
"""


@pytest.fixture()
def py_310_module_content() -> str:
    return """
from __future__ import annotations

from msgspec import Struct

from litestar import Litestar, get

class A(Struct):
    a: A
    b: B
    opt_a: A | None = None
    opt_b: B | None = None
    list_a: list[A] = []
    list_b: list[B] = []

class B(Struct):
    a: A
    b: B
    opt_a: A | None = None
    opt_b: B | None = None
    list_a: list[A] = []
    list_b: list[B] = []

@get("/")
async def test() -> A:
    return A()
"""


@pytest.mark.parametrize(
    ("fixture_name",),
    [
        ("py_38_module_content",),
        pytest.param(
            "py_310_module_content",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 10),
                reason="requires python 3.10",
            ),
        ),
    ],
)
def test_recursive_schema_generation(
    fixture_name: str, create_module: Callable[[str], ModuleType], request: pytest.FixtureRequest
) -> None:
    module_content = request.getfixturevalue(fixture_name)
    module = create_module(module_content)
    with create_test_client(module.test, debug=True) as client:
        schema = client.app.openapi_schema
        assert schema
        assert schema.to_schema()["components"]["schemas"]["A"] == {
            "required": ["a", "b"],
            "properties": {
                "a": {"$ref": "#/components/schemas/A"},
                "b": {"$ref": "#/components/schemas/B"},
                "opt_a": {"oneOf": [{"type": "null"}, {"$ref": "#/components/schemas/A"}]},
                "opt_b": {"oneOf": [{"type": "null"}, {"$ref": "#/components/schemas/B"}]},
                "list_a": {"items": {"$ref": "#/components/schemas/A"}, "type": "array"},
                "list_b": {"items": {"$ref": "#/components/schemas/B"}, "type": "array"},
            },
            "type": "object",
            "title": "A",
        }
        assert schema.to_schema()["components"]["schemas"]["B"] == {
            "required": ["a", "b"],
            "properties": {
                "a": {"$ref": "#/components/schemas/A"},
                "b": {"$ref": "#/components/schemas/B"},
                "opt_a": {"oneOf": [{"type": "null"}, {"$ref": "#/components/schemas/A"}]},
                "opt_b": {"oneOf": [{"type": "null"}, {"$ref": "#/components/schemas/B"}]},
                "list_a": {"items": {"$ref": "#/components/schemas/A"}, "type": "array"},
                "list_b": {"items": {"$ref": "#/components/schemas/B"}, "type": "array"},
            },
            "type": "object",
            "title": "B",
        }
