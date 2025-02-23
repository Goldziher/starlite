from typing import Optional

import attrs

from litestar import post
from litestar.testing import create_test_client
from tests.models import DataclassPet


def test_spec_generation() -> None:
    @attrs.define
    class Person:
        first_name: str
        last_name: str
        id: str
        optional: Optional[str]
        complex: dict[str, list[dict[str, str]]]
        pets: Optional[list[DataclassPet]]

    @post("/")
    def handler(data: Person) -> Person:
        return data

    with create_test_client(handler) as client:
        schema = client.app.openapi_schema
        assert schema
        assert schema.to_schema()["components"]["schemas"]["test_spec_generation.Person"] == {
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "id": {"type": "string"},
                "optional": {"oneOf": [{"type": "string"}, {"type": "null"}]},
                "complex": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": {"type": "string"}},
                    },
                },
                "pets": {
                    "oneOf": [
                        {
                            "items": {"$ref": "#/components/schemas/DataclassPet"},
                            "type": "array",
                        },
                        {"type": "null"},
                    ]
                },
            },
            "type": "object",
            "required": ["complex", "first_name", "id", "last_name"],
            "title": "Person",
        }
