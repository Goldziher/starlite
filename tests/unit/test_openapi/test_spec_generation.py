from typing import Any

import pytest
from msgspec import Struct

from litestar import post
from litestar._openapi.schema_generation.utils import _get_normalized_schema_key
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
        schema_key = _get_normalized_schema_key(str(cls))

        assert schema.to_schema()["components"]["schemas"][schema_key] == {
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
                            "items": {"$ref": "#/components/schemas/_class__tests_models_DataclassPet__"},
                            "type": "array",
                        },
                    ]
                },
            },
            "type": "object",
            "required": ["complex", "first_name", "id", "last_name"],
            "title": f"{cls.__name__}",
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

        assert schema.to_schema()["components"]["schemas"][
            "_class__tests_unit_test_openapi_test_spec_generation_test_msgspec_schema__locals__CamelizedStruct__"
        ] == {
            "properties": {"fieldOne": {"type": "integer"}, "fieldTwo": {"type": "number"}},
            "required": ["fieldOne", "fieldTwo"],
            "title": "CamelizedStruct",
            "type": "object",
        }
