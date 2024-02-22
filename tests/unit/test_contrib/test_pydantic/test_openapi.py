from datetime import date, datetime, timedelta
from decimal import Decimal
from types import ModuleType
from typing import Any, Callable, Pattern, Type, Union, cast

import pydantic as pydantic_v2
import pytest
from pydantic import v1 as pydantic_v1
from typing_extensions import Annotated

from litestar import Litestar, post
from litestar._openapi.schema_generation.constrained_fields import (
    create_date_constrained_field_schema,
    create_numerical_constrained_field_schema,
    create_string_constrained_field_schema,
)
from litestar._openapi.schema_generation.schema import SchemaCreator
from litestar.contrib.pydantic import PydanticPlugin, PydanticSchemaPlugin
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Example, Reference, Schema
from litestar.openapi.spec.enums import OpenAPIFormat, OpenAPIType
from litestar.params import KwargDefinition
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient, create_test_client
from litestar.typing import FieldDefinition
from litestar.utils import is_class_and_subclass
from tests.helpers import get_schema_for_field_definition
from tests.unit.test_contrib.test_pydantic.models import (
    PydanticDataclassPerson,
    PydanticPerson,
    PydanticV1DataclassPerson,
    PydanticV1Person,
)

from . import PydanticVersion

AnyBaseModelType = Type[Union[pydantic_v1.BaseModel, pydantic_v2.BaseModel]]


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


@pytest.mark.parametrize("annotation", constrained_collection_v1)
def test_create_collection_constrained_field_schema_pydantic_v1(annotation: Any) -> None:
    schema = SchemaCreator().for_collection_constrained_field(FieldDefinition.from_annotation(annotation))
    assert schema.type == OpenAPIType.ARRAY
    assert schema.items.type == OpenAPIType.INTEGER  # type: ignore[union-attr]
    assert schema.min_items == annotation.min_items
    assert schema.max_items == annotation.max_items


@pytest.mark.parametrize("annotation", constrained_collection_v2)
def test_create_collection_constrained_field_schema_pydantic_v2(annotation: Any) -> None:
    field_definition = FieldDefinition.from_annotation(annotation)
    schema = SchemaCreator().for_collection_constrained_field(field_definition)
    assert schema.type == OpenAPIType.ARRAY
    assert schema.items.type == OpenAPIType.INTEGER  # type: ignore[union-attr]
    assert any(getattr(m, "min_length", None) == schema.min_items for m in field_definition.metadata if m)
    assert any(getattr(m, "max_length", None) == schema.max_items for m in field_definition.metadata if m)


@pytest.fixture()
def conset(pydantic_version: PydanticVersion) -> Any:
    return pydantic_v1.conset if pydantic_version == "v1" else pydantic_v2.conset


@pytest.fixture()
def conlist(pydantic_version: PydanticVersion) -> Any:
    return pydantic_v1.conlist if pydantic_version == "v1" else pydantic_v2.conlist


def test_create_collection_constrained_field_schema_sub_fields(
    pydantic_version: PydanticVersion, conset: Any, conlist: Any
) -> None:
    for pydantic_fn in [conset, conlist]:
        if pydantic_version == "v1":
            annotation = pydantic_fn(Union[str, int], min_items=1, max_items=10)
        else:
            annotation = pydantic_fn(Union[str, int], min_length=1, max_length=10)
        field_definition = FieldDefinition.from_annotation(annotation)
        schema = SchemaCreator().for_collection_constrained_field(field_definition)
        assert schema.type == OpenAPIType.ARRAY
        assert schema.max_items == 10
        assert schema.min_items == 1
        assert isinstance(schema.items, Schema)
        assert schema.items.one_of is not None

        def _get_schema_type(s: Any) -> OpenAPIType:
            assert isinstance(s, Schema)
            assert isinstance(s.type, OpenAPIType)
            return s.type

        # https://github.com/litestar-org/litestar/pull/2570#issuecomment-1788122570
        assert {_get_schema_type(s) for s in schema.items.one_of} == {OpenAPIType.STRING, OpenAPIType.INTEGER}
        if pydantic_fn is conset:
            # set should have uniqueItems always
            assert schema.unique_items


@pytest.mark.parametrize("annotation", constrained_string_v1)
def test_create_string_constrained_field_schema_pydantic_v1(annotation: Any) -> None:
    field_definition = FieldDefinition.from_annotation(annotation)

    assert isinstance(field_definition.kwarg_definition, KwargDefinition)
    schema = create_string_constrained_field_schema(field_definition.annotation, field_definition.kwarg_definition)
    assert schema.type == OpenAPIType.STRING

    assert schema.min_length == annotation.min_length
    assert schema.max_length == annotation.max_length
    if pattern := getattr(annotation, "regex", None):
        assert schema.pattern == pattern.pattern if isinstance(pattern, Pattern) else pattern
    if annotation.to_lower:
        assert schema.description
    if annotation.to_upper:
        assert schema.description


@pytest.mark.parametrize("annotation", constrained_string_v2)
def test_create_string_constrained_field_schema_pydantic_v2(annotation: Any) -> None:
    field_definition = FieldDefinition.from_annotation(annotation)

    assert isinstance(field_definition.kwarg_definition, KwargDefinition)
    schema = create_string_constrained_field_schema(field_definition.annotation, field_definition.kwarg_definition)
    assert schema.type == OpenAPIType.STRING

    assert any(getattr(m, "min_length", None) == schema.min_length for m in field_definition.metadata if m)
    assert any(getattr(m, "max_length", None) == schema.max_length for m in field_definition.metadata if m)
    if pattern := getattr(annotation, "regex", getattr(annotation, "pattern", None)):
        assert schema.pattern == pattern.pattern if isinstance(pattern, Pattern) else pattern
    if any(getattr(m, "to_lower", getattr(m, "to_upper", None)) for m in field_definition.metadata if m):
        assert schema.description


@pytest.mark.parametrize("annotation", constrained_numbers_v1)
def test_create_numerical_constrained_field_schema_pydantic_v1(annotation: Any) -> None:
    from pydantic.v1.types import ConstrainedDecimal, ConstrainedFloat, ConstrainedInt

    annotation = cast(Union[ConstrainedInt, ConstrainedFloat, ConstrainedDecimal], annotation)

    field_definition = FieldDefinition.from_annotation(annotation)

    assert isinstance(field_definition.kwarg_definition, KwargDefinition)
    schema = create_numerical_constrained_field_schema(field_definition.annotation, field_definition.kwarg_definition)
    assert (
        schema.type == OpenAPIType.INTEGER if is_class_and_subclass(annotation, ConstrainedInt) else OpenAPIType.NUMBER
    )
    assert schema.exclusive_minimum == annotation.gt
    assert schema.minimum == annotation.ge
    assert schema.exclusive_maximum == annotation.lt
    assert schema.maximum == annotation.le
    assert schema.multiple_of == annotation.multiple_of


@pytest.mark.parametrize("annotation", constrained_numbers_v2)
def test_create_numerical_constrained_field_schema_pydantic_v2(annotation: Any) -> None:
    field_definition = FieldDefinition.from_annotation(annotation)

    assert isinstance(field_definition.kwarg_definition, KwargDefinition)
    schema = create_numerical_constrained_field_schema(field_definition.annotation, field_definition.kwarg_definition)
    assert schema.type == OpenAPIType.INTEGER if is_class_and_subclass(annotation, int) else OpenAPIType.NUMBER
    assert any(getattr(m, "gt", None) == schema.exclusive_minimum for m in field_definition.metadata if m)
    assert any(getattr(m, "ge", None) == schema.minimum for m in field_definition.metadata if m)
    assert any(getattr(m, "lt", None) == schema.exclusive_maximum for m in field_definition.metadata if m)
    assert any(getattr(m, "le", None) == schema.maximum for m in field_definition.metadata if m)
    assert any(getattr(m, "multiple_of", None) == schema.multiple_of for m in field_definition.metadata if m)


@pytest.mark.parametrize("annotation", constrained_dates_v1)
def test_create_date_constrained_field_schema_pydantic_v1(annotation: Any) -> None:
    field_definition = FieldDefinition.from_annotation(annotation)

    assert isinstance(field_definition.kwarg_definition, KwargDefinition)
    schema = create_date_constrained_field_schema(field_definition.annotation, field_definition.kwarg_definition)
    assert schema.type == OpenAPIType.STRING
    assert schema.format == OpenAPIFormat.DATE
    assert (datetime.utcfromtimestamp(schema.exclusive_minimum) if schema.exclusive_minimum else None) == (
        datetime.fromordinal(annotation.gt.toordinal()) if annotation.gt is not None else None
    )
    assert (datetime.utcfromtimestamp(schema.minimum) if schema.minimum else None) == (
        datetime.fromordinal(annotation.ge.toordinal()) if annotation.ge is not None else None
    )
    assert (datetime.utcfromtimestamp(schema.exclusive_maximum) if schema.exclusive_maximum else None) == (
        datetime.fromordinal(annotation.lt.toordinal()) if annotation.lt is not None else None
    )
    assert (datetime.utcfromtimestamp(schema.maximum) if schema.maximum else None) == (
        datetime.fromordinal(annotation.le.toordinal()) if annotation.le is not None else None
    )


@pytest.mark.parametrize("annotation", constrained_dates_v2)
def test_create_date_constrained_field_schema_pydantic_v2(annotation: Any) -> None:
    field_definition = FieldDefinition.from_annotation(annotation)

    assert isinstance(field_definition.kwarg_definition, KwargDefinition)
    schema = create_date_constrained_field_schema(field_definition.annotation, field_definition.kwarg_definition)
    assert schema.type == OpenAPIType.STRING
    assert schema.format == OpenAPIFormat.DATE
    assert any(
        (datetime.fromordinal(getattr(m, "gt", None).toordinal()) if getattr(m, "gt", None) is not None else None)  # type: ignore[union-attr]
        == (datetime.utcfromtimestamp(schema.exclusive_minimum) if schema.exclusive_minimum else None)
        for m in field_definition.metadata
        if m
    )
    assert any(
        (datetime.fromordinal(getattr(m, "ge", None).toordinal()) if getattr(m, "ge", None) is not None else None)  # type: ignore[union-attr]
        == (datetime.utcfromtimestamp(schema.minimum) if schema.minimum else None)
        for m in field_definition.metadata
        if m
    )
    assert any(
        (datetime.fromordinal(getattr(m, "lt", None).toordinal()) if getattr(m, "lt", None) is not None else None)  # type: ignore[union-attr]
        == (datetime.utcfromtimestamp(schema.exclusive_maximum) if schema.exclusive_maximum else None)
        for m in field_definition.metadata
        if m
    )
    assert any(
        (datetime.fromordinal(getattr(m, "le", None).toordinal()) if getattr(m, "le", None) is not None else None)  # type: ignore[union-attr]
        == (datetime.utcfromtimestamp(schema.maximum) if schema.maximum else None)
        for m in field_definition.metadata
        if m
    )


@pytest.mark.parametrize(
    "annotation",
    [
        *constrained_numbers_v1,
        *constrained_collection_v1,
        *constrained_string_v1,
        *constrained_dates_v1,
        *constrained_numbers_v2,
        *constrained_collection_v2,
        *constrained_string_v2,
        *constrained_dates_v2,
    ],
)
def test_create_constrained_field_schema(annotation: Any) -> None:
    schema = SchemaCreator().for_constrained_field(FieldDefinition.from_annotation(annotation))
    assert schema


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


@pytest.mark.parametrize("create_examples", (True, False))
def test_schema_generation_v1(create_examples: bool) -> None:
    class Lookup(pydantic_v1.BaseModel):
        id: Annotated[
            str,
            pydantic_v1.Field(
                min_length=12,
                max_length=16,
                description="A unique identifier",
                example="e4eaaaf2-d142-11e1-b3e4-080027620cdd",  # pyright: ignore
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
        ),
        signature_namespace={"Lookup": Lookup},
    ) as client:
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_200_OK
        assert response.json()["components"]["schemas"]["test_schema_generation_v1.Lookup"]["properties"]["id"] == {
            "description": "A unique identifier",
            "examples": {"id-example-1": {"value": "e4eaaaf2-d142-11e1-b3e4-080027620cdd"}},
            "maxLength": 16,
            "minLength": 12,
            "type": "string",
        }


@pytest.mark.parametrize("create_examples", (True, False))
def test_schema_generation_v2(create_examples: bool) -> None:
    class Lookup(pydantic_v2.BaseModel):
        id: Annotated[
            str,
            pydantic_v2.Field(
                min_length=12,
                max_length=16,
                description="A unique identifier",
                json_schema_extra={"example": "e4eaaaf2-d142-11e1-b3e4-080027620cdd"},
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
        ),
        signature_namespace={"Lookup": Lookup},
    ) as client:
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_200_OK
        assert response.json()["components"]["schemas"]["test_schema_generation_v2.Lookup"]["properties"]["id"] == {
            "description": "A unique identifier",
            "examples": {"id-example-1": {"value": "e4eaaaf2-d142-11e1-b3e4-080027620cdd"}},
            "maxLength": 16,
            "minLength": 12,
            "type": "string",
        }


def test_schema_by_alias(base_model: AnyBaseModelType, pydantic_version: PydanticVersion) -> None:
    class RequestWithAlias(base_model):  # type: ignore[misc, valid-type]
        first: str = (pydantic_v1.Field if pydantic_version == "v1" else pydantic_v2.Field)(alias="second")  # type: ignore[operator]

    class ResponseWithAlias(base_model):  # type: ignore[misc, valid-type]
        first: str = (pydantic_v1.Field if pydantic_version == "v1" else pydantic_v2.Field)(alias="second")  # type: ignore[operator]

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
        first: str = (pydantic_v1.Field if pydantic_version == "v1" else pydantic_v2.Field)(alias="second")  # type: ignore[operator]

    class ResponseWithAlias(base_model):  # type: ignore[misc, valid-type]
        first: str = (pydantic_v1.Field if pydantic_version == "v1" else pydantic_v2.Field)(alias="second")  # type: ignore[operator]

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
    assert value.examples == {"value-example-1": Example(value="example")}


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
    assert value.examples == {"value-example-1": Example(value="example")}


@pytest.mark.parametrize("with_future_annotations", [True, False])
def test_create_schema_for_pydantic_model_with_annotated_model_attribute(
    with_future_annotations: bool, create_module: "Callable[[str], ModuleType]", pydantic_version: PydanticVersion
) -> None:
    """Test that a model with an annotated attribute is correctly handled."""
    module = create_module(
        f"""
{'from __future__ import annotations' if with_future_annotations else ''}
from typing_extensions import Annotated
{'from pydantic import BaseModel' if pydantic_version == 'v1' else 'from pydantic.v1 import BaseModel'}

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
