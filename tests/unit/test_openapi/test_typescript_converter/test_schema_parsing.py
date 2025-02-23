import string
from typing import Any

import pytest

from litestar._openapi.typescript_converter.schema_parsing import normalize_typescript_namespace, parse_schema
from litestar._openapi.typescript_converter.types import TypeScriptIntersection
from litestar.openapi.spec import Schema
from litestar.openapi.spec.enums import OpenAPIType

object_schema_1 = Schema(
    type=OpenAPIType.OBJECT,
    properties={
        "first_1": Schema(
            type=OpenAPIType.STRING,
        ),
        "second_1": Schema(type=[OpenAPIType.NUMBER, OpenAPIType.NULL]),
    },
    required=["first_1"],
)

object_schema_2 = Schema(
    type=OpenAPIType.OBJECT,
    properties={
        "first_2": Schema(
            type=OpenAPIType.BOOLEAN,
        ),
        "second_2": Schema(
            type=OpenAPIType.INTEGER,
        ),
    },
    required=["first_2"],
)

string_schema = Schema(type=[OpenAPIType.STRING])
number_schema = Schema(type=[OpenAPIType.NUMBER])
nullable_integer_schema = Schema(type=[OpenAPIType.INTEGER, OpenAPIType.NULL])
array_schema = Schema(type=OpenAPIType.ARRAY, items=Schema(one_of=[object_schema_1, object_schema_2]))


def test_parse_schema_handle_all_of() -> None:
    result = parse_schema(Schema(all_of=[object_schema_1, object_schema_2]))
    assert isinstance(result, TypeScriptIntersection)
    assert (
        result.write()
        == "{\n\tfirst_1: string;\n\tsecond_1?: null | number;\n} & {\n\tfirst_2: boolean;\n\tsecond_2?: number;\n}"
    )


def test_parse_schema_handle_one_of() -> None:
    result = parse_schema(
        Schema(one_of=[object_schema_1, object_schema_2, number_schema, string_schema, nullable_integer_schema])
    )
    assert (
        result.write() == "null | number | number | string | {\n"
        "\tfirst_1: string;\n"
        "\tsecond_1?: null | number;\n"
        "} | {\n"
        "\tfirst_2: boolean;\n"
        "\tsecond_2?: number;\n"
        "}"
    )


def test_parse_schema_handle_array() -> None:
    result = parse_schema(array_schema)
    assert (
        result.write()
        == "({\n\tfirst_1: string;\n\tsecond_1?: null | number;\n} | {\n\tfirst_2: boolean;\n\tsecond_2?: number;\n})[]"
    )


def test_parse_schema_handle_object() -> None:
    result = parse_schema(object_schema_1)
    assert result.write() == "{\n\tfirst_1: string;\n\tsecond_1?: null | number;\n}"


@pytest.mark.parametrize(
    "schema_type, enum, expected",
    (
        (OpenAPIType.STRING, ["a", "b", "c"], '"a" | "b" | "c"'),
        (OpenAPIType.NUMBER, [1, 2, 3], "1 | 2 | 3"),
        (
            [OpenAPIType.NULL, OpenAPIType.BOOLEAN, OpenAPIType.STRING],
            [None, True, False, "moishe"],
            '"moishe" | false | null | true',
        ),
    ),
)
def test_parse_schema_handle_enum(schema_type: Any, enum: list[Any], expected: str) -> None:
    result = parse_schema(Schema(type=schema_type, enum=enum))
    assert result.write() == expected


@pytest.mark.parametrize("namespace", [string.punctuation])
def test_normalize_typescript_namespace_invalid_namespace_raises(namespace: str) -> None:
    with pytest.raises(ValueError):
        normalize_typescript_namespace(namespace, False)
