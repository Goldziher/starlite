# pyright: reportOptionalSubscript=false, reportGeneralTypeIssues=false
from datetime import date, timedelta
from decimal import Decimal
from re import Pattern
from types import ModuleType
from typing import Annotated, Any, Callable, Optional, Union, cast

import annotated_types
import pydantic as pydantic_v2
import pytest
from pydantic import v1 as pydantic_v1

from litestar import Litestar, get, post
from litestar._openapi.schema_generation.schema import SchemaCreator
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Reference, Schema
from litestar.openapi.spec.enums import OpenAPIFormat, OpenAPIType
from litestar.plugins.pydantic import PydanticPlugin, PydanticSchemaPlugin
from litestar.testing import TestClient, create_test_client
from litestar.typing import FieldDefinition
from litestar.utils import is_class_and_subclass
from tests.helpers import get_schema_for_field_definition
from tests.unit.test_plugins.test_pydantic.models import (
    PydanticDataclassPerson,
    PydanticPerson,
    PydanticV1DataclassPerson,
    PydanticV1Person,
)

from . import PydanticVersion

AnyBaseModelType = type[Union[pydantic_v1.BaseModel, pydantic_v2.BaseModel]]


constrained_string_v1 = [
    pydantic_v1.constr(regex="^[a-zA-Z]$"),
    pydantic_v1.constr(to_upper=True, min_length=1, regex="^[a-zA-Z]$"),
    pydantic_v1.constr(to_lower=True, min_length=1, regex="^[a-zA-Z]$"),
    pydantic_v1.constr(to_lower=True, min_length=10, regex="^[a-zA-Z]$"),
    pydantic_v1.constr(to_lower=True, min_length=10, max_length=100, regex="^[a-zA-Z]$"),
    pydantic_v1.constr(min_length=1),
    pydantic_v1.constr(min_length=10),
    pydantic_v1.constr(min_length=10, max_length=100),
    pydantic_v1.conbytes(min_length=1),
    pydantic_v1.conbytes(min_length=10),
    pydantic_v1.conbytes(min_length=10, max_length=100),
]

constrained_string_v2 = [
    pydantic_v2.constr(pattern="^[a-zA-Z]$"),
    pydantic_v2.constr(to_upper=True, min_length=1, pattern="^[a-zA-Z]$"),
    pydantic_v2.constr(to_lower=True, min_length=1, pattern="^[a-zA-Z]$"),
    pydantic_v2.constr(to_lower=True, min_length=10, pattern="^[a-zA-Z]$"),
    pydantic_v2.constr(to_lower=True, min_length=10, max_length=100, pattern="^[a-zA-Z]$"),
    pydantic_v2.constr(min_length=1),
    pydantic_v2.constr(min_length=10),
    pydantic_v2.constr(min_length=10, max_length=100),
]

constrained_bytes_v2 = [
    pydantic_v2.conbytes(min_length=1),
    pydantic_v2.conbytes(min_length=10),
    pydantic_v2.conbytes(min_length=10, max_length=100),
]


constrained_collection_v1 = [
    pydantic_v1.conlist(int, min_items=1),
    pydantic_v1.conlist(int, min_items=1, max_items=10),
    pydantic_v1.conset(int, min_items=1),
    pydantic_v1.conset(int, min_items=1, max_items=10),
]

constrained_collection_v2 = [
    pydantic_v2.conlist(int, min_length=1),
    pydantic_v2.conlist(int, min_length=1, max_length=10),
    pydantic_v2.conset(int, min_length=1),
    pydantic_v2.conset(int, min_length=1, max_length=10),
]

constrained_numbers_v1 = [
    pydantic_v1.conint(gt=10, lt=100),
    pydantic_v1.conint(ge=10, le=100),
    pydantic_v1.conint(ge=10, le=100, multiple_of=7),
    pydantic_v1.confloat(gt=10, lt=100),
    pydantic_v1.confloat(ge=10, le=100),
    pydantic_v1.confloat(ge=10, le=100, multiple_of=4.2),
    pydantic_v1.confloat(gt=10, lt=100, multiple_of=10),
    pydantic_v1.condecimal(gt=Decimal("10"), lt=Decimal("100")),
    pydantic_v1.condecimal(ge=Decimal("10"), le=Decimal("100")),
    pydantic_v1.condecimal(gt=Decimal("10"), lt=Decimal("100"), multiple_of=Decimal("5")),
    pydantic_v1.condecimal(ge=Decimal("10"), le=Decimal("100"), multiple_of=Decimal("2")),
]

constrained_numbers_v2 = [
    pydantic_v2.conint(gt=10, lt=100),
    pydantic_v2.conint(ge=10, le=100),
    pydantic_v2.conint(ge=10, le=100, multiple_of=7),
    pydantic_v2.confloat(gt=10, lt=100),
    pydantic_v2.confloat(ge=10, le=100),
    pydantic_v2.confloat(ge=10, le=100, multiple_of=4.2),
    pydantic_v2.confloat(gt=10, lt=100, multiple_of=10),
    pydantic_v2.condecimal(gt=Decimal("10"), lt=Decimal("100")),
    pydantic_v2.condecimal(ge=Decimal("10"), le=Decimal("100")),
    pydantic_v2.condecimal(gt=Decimal("10"), lt=Decimal("100"), multiple_of=Decimal("5")),
    pydantic_v2.condecimal(ge=Decimal("10"), le=Decimal("100"), multiple_of=Decimal("2")),
]


constrained_dates_v1 = [
    pydantic_v1.condate(gt=date.today() - timedelta(days=10), lt=date.today() + timedelta(days=100)),
    pydantic_v1.condate(ge=date.today() - timedelta(days=10), le=date.today() + timedelta(days=100)),
    pydantic_v1.condate(gt=date.today() - timedelta(days=10), lt=date.today() + timedelta(days=100)),
    pydantic_v1.condate(ge=date.today() - timedelta(days=10), le=date.today() + timedelta(days=100)),
]

constrained_dates_v2 = [
    pydantic_v2.condate(gt=date.today() - timedelta(days=10), lt=date.today() + timedelta(days=100)),
    pydantic_v2.condate(ge=date.today() - timedelta(days=10), le=date.today() + timedelta(days=100)),
    pydantic_v2.condate(gt=date.today() - timedelta(days=10), lt=date.today() + timedelta(days=100)),
    pydantic_v2.condate(ge=date.today() - timedelta(days=10), le=date.today() + timedelta(days=100)),
]


@pytest.fixture()
def schema_creator(plugin: PydanticSchemaPlugin) -> SchemaCreator:
    return SchemaCreator(plugins=[plugin])


@pytest.fixture()
def plugin() -> PydanticSchemaPlugin:
    return PydanticSchemaPlugin()


@pytest.mark.parametrize("annotation", constrained_collection_v1)
def test_create_collection_constrained_field_schema_pydantic_v1(
    annotation: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    class Model(pydantic_v1.BaseModel):
        field: annotation

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert schema.type == OpenAPIType.ARRAY  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.items.type == OpenAPIType.INTEGER  # type: ignore[union-attr] # pyright: ignore[reportAttributeAccessIssue]
    assert schema.min_items == annotation.min_items  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.max_items == annotation.max_items  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize("make_constraint", [pydantic_v2.conlist, pydantic_v2.conset, pydantic_v2.confrozenset])
@pytest.mark.parametrize(
    "min_length, max_length",
    [
        (None, None),
        (1, None),
        (1, 1),
        (None, 1),
    ],
)
def test_create_collection_constrained_field_schema_pydantic_v2(
    make_constraint: Callable[..., Any],
    min_length: Optional[int],
    max_length: Optional[int],
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    class Model(pydantic_v2.BaseModel):
        field: make_constraint(int, min_length=min_length, max_length=max_length)  # type: ignore[valid-type]

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert schema.type == OpenAPIType.ARRAY  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.items.type == OpenAPIType.INTEGER  # type: ignore[union-attr]
    assert schema.min_items == min_length  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.max_items == max_length  # pyright: ignore[reportAttributeAccessIssue]


@pytest.fixture()
def conset(pydantic_version: PydanticVersion) -> Any:
    return pydantic_v1.conset if pydantic_version == "v1" else pydantic_v2.conset


@pytest.fixture()
def conlist(pydantic_version: PydanticVersion) -> Any:
    return pydantic_v1.conlist if pydantic_version == "v1" else pydantic_v2.conlist


def test_create_collection_constrained_field_schema_sub_fields(
    pydantic_version: PydanticVersion,
    conset: Any,
    conlist: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    if pydantic_version == "v1":

        class Modelv1(pydantic_v1.BaseModel):
            set_field: conset(Union[str, int], min_items=1, max_items=10)  # type: ignore[valid-type]
            list_field: conlist(Union[str, int], min_items=1, max_items=10)  # type: ignore[valid-type]

        model_schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Modelv1), plugin)
    else:

        class Modelv2(pydantic_v2.BaseModel):
            set_field: conset(Union[str, int], min_length=1, max_length=10)  # type: ignore[valid-type]
            list_field: conlist(Union[str, int], min_length=1, max_length=10)  # type: ignore[valid-type]

        model_schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Modelv2), plugin)

    def _get_schema_type(s: Any) -> OpenAPIType:
        assert isinstance(s, Schema)
        assert isinstance(s.type, OpenAPIType)
        return s.type

    for field_name in ["set_field", "list_field"]:
        schema = model_schema.properties[field_name]  # pyright: ignore[reportAttributeAccessIssue]

        assert schema.type == OpenAPIType.ARRAY  # pyright: ignore[reportAttributeAccessIssue]
        assert schema.max_items == 10  # pyright: ignore[reportAttributeAccessIssue]
        assert schema.min_items == 1  # pyright: ignore[reportAttributeAccessIssue]
        assert isinstance(schema.items, Schema)  # pyright: ignore[reportAttributeAccessIssue]
        assert schema.items.one_of is not None  # pyright: ignore[reportAttributeAccessIssue]

        # https://github.com/litestar-org/litestar/pull/2570#issuecomment-1788122570
        assert {_get_schema_type(s) for s in schema.items.one_of} == {OpenAPIType.STRING, OpenAPIType.INTEGER}  # pyright: ignore[reportAttributeAccessIssue]

    # set should have uniqueItems always
    assert model_schema.properties["set_field"].unique_items  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize("annotation", constrained_string_v1)
def test_create_string_constrained_field_schema_pydantic_v1(
    annotation: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    class Model(pydantic_v1.BaseModel):
        field: annotation

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert schema.type == OpenAPIType.STRING  # pyright: ignore[reportAttributeAccessIssue]

    assert schema.min_length == annotation.min_length  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.max_length == annotation.max_length  # pyright: ignore[reportAttributeAccessIssue]
    if pattern := getattr(annotation, "regex", None):
        assert schema.pattern == pattern.pattern if isinstance(pattern, Pattern) else pattern  # pyright: ignore[reportAttributeAccessIssue]
    if annotation.to_lower:
        assert schema.description
    if annotation.to_upper:
        assert schema.description


@pytest.mark.parametrize("annotation", constrained_string_v2)
def test_create_string_constrained_field_schema_pydantic_v2(
    annotation: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    constraint: pydantic_v2.types.StringConstraints = annotation.__metadata__[0]

    class Model(pydantic_v2.BaseModel):
        field: annotation

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert schema.type == OpenAPIType.STRING  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.min_length == constraint.min_length  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.max_length == constraint.max_length  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.pattern == constraint.pattern  # pyright: ignore[reportAttributeAccessIssue]
    if constraint.to_upper:
        assert schema.description == "must be in upper case"
    if constraint.to_lower:
        assert schema.description == "must be in lower case"


@pytest.mark.parametrize("annotation", constrained_bytes_v2)
def test_create_byte_constrained_field_schema_pydantic_v2(
    annotation: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    constraint: annotated_types.Len = annotation.__metadata__[1]

    class Model(pydantic_v2.BaseModel):
        field: annotation

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert schema.type == OpenAPIType.STRING  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.min_length == constraint.min_length  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.max_length == constraint.max_length  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize("annotation", constrained_numbers_v1)
def test_create_numerical_constrained_field_schema_pydantic_v1(
    annotation: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    from pydantic.v1.types import ConstrainedDecimal, ConstrainedFloat, ConstrainedInt

    annotation = cast(Union[ConstrainedInt, ConstrainedFloat, ConstrainedDecimal], annotation)

    class Model(pydantic_v1.BaseModel):
        field: annotation

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert (
        schema.type == OpenAPIType.INTEGER if is_class_and_subclass(annotation, ConstrainedInt) else OpenAPIType.NUMBER  # pyright: ignore[reportAttributeAccessIssue]
    )
    assert schema.exclusive_minimum == annotation.gt  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.minimum == annotation.ge  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.exclusive_maximum == annotation.lt  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.maximum == annotation.le  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.multiple_of == annotation.multiple_of  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize(
    "make_constraint, constraint_kwargs",
    [
        (pydantic_v2.conint, {"gt": 10, "lt": 100}),
        (pydantic_v2.conint, {"ge": 10, "le": 100}),
        (pydantic_v2.conint, {"ge": 10, "le": 100, "multiple_of": 7}),
        (pydantic_v2.confloat, {"gt": 10, "lt": 100}),
        (pydantic_v2.confloat, {"ge": 10, "le": 100}),
        (pydantic_v2.confloat, {"ge": 10, "le": 100, "multiple_of": 4.2}),
        (pydantic_v2.confloat, {"gt": 10, "lt": 100, "multiple_of": 10}),
        (pydantic_v2.condecimal, {"gt": Decimal("10"), "lt": Decimal("100")}),
        (pydantic_v2.condecimal, {"ge": Decimal("10"), "le": Decimal("100")}),
        (pydantic_v2.condecimal, {"gt": Decimal("10"), "lt": Decimal("100"), "multiple_of": Decimal("5")}),
        (pydantic_v2.condecimal, {"ge": Decimal("10"), "le": Decimal("100"), "multiple_of": Decimal("2")}),
    ],
)
def test_create_numerical_constrained_field_schema_pydantic_v2(
    make_constraint: Any,
    constraint_kwargs: dict[str, Any],
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    annotation = make_constraint(**constraint_kwargs)

    class Model(pydantic_v1.BaseModel):
        field: annotation  # type: ignore[valid-type]

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert schema.type == OpenAPIType.INTEGER if is_class_and_subclass(annotation, int) else OpenAPIType.NUMBER  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.exclusive_minimum == constraint_kwargs.get("gt")  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.minimum == constraint_kwargs.get("ge")  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.exclusive_maximum == constraint_kwargs.get("lt")  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.maximum == constraint_kwargs.get("le")  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.multiple_of == constraint_kwargs.get("multiple_of")  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize("annotation", constrained_dates_v1)
def test_create_date_constrained_field_schema_pydantic_v1(
    annotation: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    class Model(pydantic_v1.BaseModel):
        field: annotation

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert schema.type == OpenAPIType.STRING  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.format == OpenAPIFormat.DATE  # pyright: ignore[reportAttributeAccessIssue]
    if gt := annotation.gt:
        assert date.fromtimestamp(schema.exclusive_minimum) == gt  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
    if ge := annotation.ge:
        assert date.fromtimestamp(schema.minimum) == ge  # type: ignore[arg-type]
    if lt := annotation.lt:
        assert date.fromtimestamp(schema.exclusive_maximum) == lt  # type: ignore[arg-type]
    if le := annotation.le:
        assert date.fromtimestamp(schema.maximum) == le  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "constraints",
    [
        {"gt": date.today() - timedelta(days=10), "lt": date.today() + timedelta(days=100)},
        {"ge": date.today() - timedelta(days=10), "le": date.today() + timedelta(days=100)},
        {"gt": date.today() - timedelta(days=10), "lt": date.today() + timedelta(days=100)},
        {"ge": date.today() - timedelta(days=10), "le": date.today() + timedelta(days=100)},
    ],
)
def test_create_date_constrained_field_schema_pydantic_v2(
    constraints: dict[str, Any],
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    class Model(pydantic_v2.BaseModel):
        field: pydantic_v2.condate(**constraints)  # type: ignore[valid-type]

    schema = schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.type == OpenAPIType.STRING  # pyright: ignore[reportAttributeAccessIssue]
    assert schema.format == OpenAPIFormat.DATE  # pyright: ignore[reportAttributeAccessIssue]

    if gt := constraints.get("gt"):
        assert date.fromtimestamp(schema.exclusive_minimum) == gt  # type: ignore[arg-type]
    if ge := constraints.get("ge"):
        assert date.fromtimestamp(schema.minimum) == ge  # type: ignore[arg-type]
    if lt := constraints.get("lt"):
        assert date.fromtimestamp(schema.exclusive_maximum) == lt  # type: ignore[arg-type]
    if le := constraints.get("le"):
        assert date.fromtimestamp(schema.maximum) == le  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "annotation",
    [
        *constrained_numbers_v1,
        *constrained_collection_v1,
        *constrained_string_v1,
        *constrained_dates_v1,
    ],
)
def test_create_constrained_field_schema_v1(
    annotation: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    class Model(pydantic_v1.BaseModel):
        field: annotation

    assert schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize(
    "annotation",
    [
        *constrained_numbers_v2,
        *constrained_collection_v2,
        *constrained_string_v2,
        *constrained_dates_v2,
    ],
)
def test_create_constrained_field_schema_v2(
    annotation: Any,
    schema_creator: SchemaCreator,
    plugin: PydanticSchemaPlugin,
) -> None:
    class Model(pydantic_v2.BaseModel):
        field: annotation

    assert schema_creator.for_plugin(FieldDefinition.from_annotation(Model), plugin).properties["field"]  # type: ignore[index, union-attr]


@pytest.mark.parametrize("cls", (PydanticPerson, PydanticDataclassPerson, PydanticV1Person, PydanticV1DataclassPerson))
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
                "optional": {"oneOf": [{"type": "string"}, {"type": "null"}]},
                "complex": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": {"type": "string"}},
                    },
                },
                "union": {"oneOf": [{"type": "integer"}, {"items": {"type": "string"}, "type": "array"}]},
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
            "required": ["complex", "first_name", "id", "last_name", "union"],
            "title": f"{cls.__name__}",
        }


def test_schema_generation_v1() -> None:
    class Lookup(pydantic_v1.BaseModel):
        id: Annotated[
            str,
            pydantic_v1.Field(
                min_length=12,
                max_length=16,
                description="A unique identifier",
                example="e4eaaaf2-d142-11e1-b3e4-080027620cdd",  # pyright: ignore
                examples=["31", "32"],
            ),
        ]
        with_title: str = pydantic_v1.Field(title="WITH_title")

    @post("/example")
    async def example_route() -> Lookup:
        return Lookup(id="1234567812345678", with_title="1")

    app = Litestar([example_route])
    schema = app.openapi_schema.to_schema()
    lookup_schema = schema["components"]["schemas"]["test_schema_generation_v1.Lookup"]["properties"]

    assert lookup_schema["id"] == {
        "description": "A unique identifier",
        "examples": ["e4eaaaf2-d142-11e1-b3e4-080027620cdd", "31", "32"],
        "maxLength": 16,
        "minLength": 12,
        "type": "string",
    }
    assert lookup_schema["with_title"] == {"title": "WITH_title", "type": "string"}


def test_schema_generation_v2() -> None:
    class Lookup(pydantic_v2.BaseModel):
        id: Annotated[
            str,
            pydantic_v2.Field(
                min_length=12,
                max_length=16,
                description="A unique identifier",
                # we expect these examples to be merged
                json_schema_extra={"example": "e4eaaaf2-d142-11e1-b3e4-080027620cdd", "examples": ["31"]},
                examples=["32"],
            ),
        ]
        # title should work if given on the field
        with_title: str = pydantic_v2.Field(title="WITH_title")
        # or as an extra
        with_extra_title: str = pydantic_v2.Field(json_schema_extra={"title": "WITH_extra"})
        # moreover, we allow json_schema_extra to use names that exactly match the JSONSchema spec
        without_duplicates: list[str] = pydantic_v2.Field(json_schema_extra={"uniqueItems": True})

    @post("/example")
    async def example_route() -> Lookup:
        return Lookup(id="1234567812345678", with_title="1", with_extra_title="2", without_duplicates=[])

    app = Litestar([example_route])
    schema = app.openapi_schema.to_schema()
    lookup_schema = schema["components"]["schemas"]["test_schema_generation_v2.Lookup"]["properties"]

    assert lookup_schema["id"] == {
        "description": "A unique identifier",
        "examples": ["e4eaaaf2-d142-11e1-b3e4-080027620cdd", "31", "32"],
        "maxLength": 16,
        "minLength": 12,
        "type": "string",
    }
    assert lookup_schema["with_title"] == {"title": "WITH_title", "type": "string"}
    assert lookup_schema["with_extra_title"] == {"title": "WITH_extra", "type": "string"}
    assert lookup_schema["without_duplicates"] == {"type": "array", "items": {"type": "string"}, "uniqueItems": True}


def test_create_examples(pydantic_version: PydanticVersion) -> None:
    lib = pydantic_v1 if pydantic_version == "v1" else pydantic_v2

    class Model(lib.BaseModel):  # type: ignore[name-defined, misc]
        foo: str = lib.Field(examples=["32"])
        bar: str

    @get("/example")
    async def handler() -> Model:
        return Model(foo="1", bar="2")

    app = Litestar(
        [handler],
        openapi_config=OpenAPIConfig(
            title="Test",
            version="0",
            create_examples=True,
        ),
    )
    schema = app.openapi_schema.to_schema()
    lookup_schema = schema["components"]["schemas"]["test_create_examples.Model"]["properties"]

    assert lookup_schema["foo"]["examples"] == ["32"]
    assert lookup_schema["bar"]["examples"]


def test_v2_json_schema_extra_callable_raises() -> None:
    class Model(pydantic_v2.BaseModel):
        field: str = pydantic_v2.Field(json_schema_extra=lambda e: None)

    @get("/example")
    def handler() -> Model:
        return Model(field="1")

    app = Litestar([handler])
    with pytest.raises(ValueError, match="Callables not supported"):
        app.openapi_schema


def test_schema_by_alias(base_model: AnyBaseModelType, pydantic_version: PydanticVersion) -> None:
    class RequestWithAlias(base_model):  # type: ignore[valid-type,misc]
        first: str = (pydantic_v1.Field if pydantic_version == "v1" else pydantic_v2.Field)(alias="second")

    class ResponseWithAlias(base_model):  # type: ignore[valid-type,misc]
        first: str = (pydantic_v1.Field if pydantic_version == "v1" else pydantic_v2.Field)(alias="second")

    @post("/", signature_types=[RequestWithAlias, ResponseWithAlias])
    def handler(data: RequestWithAlias) -> ResponseWithAlias:
        return ResponseWithAlias(second=data.first)

    app = Litestar(route_handlers=[handler], openapi_config=OpenAPIConfig(title="my title", version="1.0.0"))

    assert app.openapi_schema
    schemas = app.openapi_schema.to_schema()["components"]["schemas"]
    request_key = "second"
    assert schemas["test_schema_by_alias.RequestWithAlias"] == {
        "properties": {request_key: {"type": "string"}},
        "type": "object",
        "required": [request_key],
        "title": "RequestWithAlias",
    }
    response_key = "first"
    assert schemas["test_schema_by_alias.ResponseWithAlias"] == {
        "properties": {response_key: {"type": "string"}},
        "type": "object",
        "required": [response_key],
        "title": "ResponseWithAlias",
    }

    with TestClient(app) as client:
        response = client.post("/", json={request_key: "foo"})
        assert response.json() == {response_key: "foo"}


def test_schema_by_alias_plugin_override(base_model: AnyBaseModelType, pydantic_version: PydanticVersion) -> None:
    class RequestWithAlias(base_model):  # type: ignore[misc, valid-type]
        first: str = (pydantic_v1.Field if pydantic_version == "v1" else pydantic_v2.Field)(alias="second")

    class ResponseWithAlias(base_model):  # type: ignore[misc, valid-type]
        first: str = (pydantic_v1.Field if pydantic_version == "v1" else pydantic_v2.Field)(alias="second")

    @post("/", signature_types=[RequestWithAlias, ResponseWithAlias])
    def handler(data: RequestWithAlias) -> ResponseWithAlias:
        return ResponseWithAlias(second=data.first)

    app = Litestar(
        route_handlers=[handler],
        openapi_config=OpenAPIConfig(title="my title", version="1.0.0"),
        plugins=[PydanticPlugin(prefer_alias=True)],
    )
    assert app.openapi_schema
    schemas = app.openapi_schema.to_schema()["components"]["schemas"]
    request_key = "second"
    assert schemas["test_schema_by_alias_plugin_override.RequestWithAlias"] == {
        "properties": {request_key: {"type": "string"}},
        "type": "object",
        "required": [request_key],
        "title": "RequestWithAlias",
    }
    response_key = "second"
    assert schemas["test_schema_by_alias_plugin_override.ResponseWithAlias"] == {
        "properties": {response_key: {"type": "string"}},
        "type": "object",
        "required": [response_key],
        "title": "ResponseWithAlias",
    }

    with TestClient(app) as client:
        response = client.post("/", json={request_key: "foo"})
        assert response.json() == {response_key: "foo"}


def test_create_schema_for_field_v1() -> None:
    class Model(pydantic_v1.BaseModel):
        value: str = pydantic_v1.Field(
            title="title",
            description="description",
            example="example",
            max_length=16,  # pyright: ignore
        )

    schema = get_schema_for_field_definition(
        FieldDefinition.from_kwarg(name="Model", annotation=Model), plugins=[PydanticSchemaPlugin()]
    )

    assert schema.properties

    value = schema.properties["value"]

    assert isinstance(value, Schema)
    assert value.description == "description"
    assert value.title == "title"
    assert value.examples == ["example"]


def test_create_schema_for_field_v2() -> None:
    class Model(pydantic_v2.BaseModel):
        value: str = pydantic_v2.Field(
            title="title", description="description", max_length=16, json_schema_extra={"example": "example"}
        )

    schema = get_schema_for_field_definition(
        FieldDefinition.from_kwarg(name="Model", annotation=Model), plugins=[PydanticSchemaPlugin()]
    )

    assert schema.properties

    value = schema.properties["value"]

    assert isinstance(value, Schema)
    assert value.description == "description"
    assert value.title == "title"
    assert value.examples == ["example"]


def test_create_schema_for_field_v2_examples() -> None:
    class Model(pydantic_v2.BaseModel):
        value: str = pydantic_v2.Field(
            title="title", description="description", max_length=16, json_schema_extra={"examples": ["example"]}
        )

    schema = get_schema_for_field_definition(
        FieldDefinition.from_kwarg(name="Model", annotation=Model), plugins=[PydanticSchemaPlugin()]
    )

    assert schema.properties

    value = schema.properties["value"]

    assert isinstance(value, Schema)
    assert value.description == "description"
    assert value.title == "title"
    assert value.examples == ["example"]


@pytest.mark.parametrize("with_future_annotations", [True, False])
def test_create_schema_for_pydantic_model_with_annotated_model_attribute(
    with_future_annotations: bool, create_module: "Callable[[str], ModuleType]", pydantic_version: PydanticVersion
) -> None:
    """Test that a model with an annotated attribute is correctly handled."""
    module = create_module(
        f"""
{'from __future__ import annotations' if with_future_annotations else ''}
from typing_extensions import Annotated
{'from pydantic import BaseModel' if pydantic_version == 'v2' else 'from pydantic.v1 import BaseModel'}

class Foo(BaseModel):
    foo: Annotated[int, "Foo description"]
"""
    )
    creator = SchemaCreator(plugins=[PydanticSchemaPlugin()])
    creator.for_field_definition(FieldDefinition.from_annotation(module.Foo))
    schemas = creator.schema_registry.generate_components_schemas()
    schema = schemas["Foo"]
    assert schema.properties and "foo" in schema.properties


def test_create_schema_for_pydantic_model_with_unhashable_literal_default(
    create_module: "Callable[[str], ModuleType]",
) -> None:
    """Test that a model with unhashable literal defaults is correctly handled."""
    module = create_module(
        """
from pydantic import BaseModel, Field

class Model(BaseModel):
    id: int
    dict_default: dict = {}
    dict_default_in_field: dict = Field(default={})
    dict_default_in_factory: dict = Field(default_factory=dict)
    list_default: list = []
    list_default_in_field: list = Field(default=[])
    list_default_in_factory: list = Field(default_factory=list)
"""
    )
    creator = SchemaCreator(plugins=[PydanticSchemaPlugin()])
    creator.for_field_definition(FieldDefinition.from_annotation(module.Model))
    schemas = creator.schema_registry.generate_components_schemas()
    schema = schemas["Model"]
    assert schema.properties
    assert "dict_default" in schema.properties
    assert "dict_default_in_field" in schema.properties
    assert "dict_default_in_factory" in schema.properties
    assert "list_default" in schema.properties
    assert "list_default_in_field" in schema.properties
    assert "list_default_in_factory" in schema.properties


@pytest.mark.parametrize("field_type", [pydantic_v2.AnyUrl, pydantic_v2.AnyHttpUrl, pydantic_v2.HttpUrl])
def test_create_for_url_v2(field_type: Any) -> None:
    field_definition = FieldDefinition.from_annotation(field_type)
    schema = SchemaCreator(plugins=[PydanticSchemaPlugin()]).for_field_definition(field_definition)
    assert schema.type == OpenAPIType.STRING  # type: ignore[union-attr]
    assert schema.format == OpenAPIFormat.URL  # type: ignore[union-attr]


@pytest.mark.parametrize("prefer_alias", [True, False])
def test_create_for_computed_field(prefer_alias: bool) -> None:
    class Sample(pydantic_v2.BaseModel):
        property_one: str

        @pydantic_v2.computed_field(
            description="a description", title="a title", alias="prop_two" if prefer_alias else None
        )
        def property_two(self) -> bool:
            return True

    field_definition = FieldDefinition.from_annotation(Sample)
    schema_creator = SchemaCreator(plugins=[PydanticSchemaPlugin()])
    ref = schema_creator.for_field_definition(field_definition)
    assert isinstance(ref, Reference)
    registered_schemas = list(schema_creator.schema_registry)
    assert len(registered_schemas) == 1
    schema = registered_schemas[0].schema
    assert schema.required == ["property_one", "property_two"] if not prefer_alias else ["property_one", "prop_two"]
    properties = schema.properties
    assert properties is not None
    assert properties.keys() == {"property_one", "property_two"} if not prefer_alias else {"property_one", "prop_two"}
    property_two = properties["property_two"] if not prefer_alias else properties["prop_two"]
    assert isinstance(property_two, Schema)
    assert property_two.type == OpenAPIType.BOOLEAN
    assert property_two.description == "a description"
    assert property_two.title == "a title"
    assert property_two.read_only
