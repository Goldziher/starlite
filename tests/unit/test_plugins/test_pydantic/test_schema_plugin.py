import datetime
from decimal import Decimal
from typing import Annotated, Any, Generic, Optional, TypeVar, Union

import pydantic as pydantic_v2
import pytest
from pydantic import v1 as pydantic_v1
from pydantic.v1.generics import GenericModel

from litestar import Litestar, post
from litestar._openapi.schema_generation import SchemaCreator
from litestar.openapi.spec import OpenAPIType
from litestar.openapi.spec.schema import Schema
from litestar.plugins.pydantic import PydanticSchemaPlugin
from litestar.typing import FieldDefinition
from litestar.utils.helpers import get_name
from tests.helpers import get_schema_for_field_definition

T = TypeVar("T")


class PydanticV1Generic(GenericModel, Generic[T]):
    foo: T
    optional_foo: Optional[T]
    annotated_foo: Annotated[T, object()]


class PydanticV2Generic(pydantic_v2.BaseModel, Generic[T]):
    foo: T
    optional_foo: Optional[T]
    annotated_foo: Annotated[T, object()]


@pytest.mark.parametrize("model", [PydanticV1Generic, PydanticV2Generic])
def test_schema_generation_with_generic_classes(model: type[Union[PydanticV1Generic, PydanticV2Generic]]) -> None:
    cls = model[int]  # type: ignore[index]
    field_definition = FieldDefinition.from_kwarg(name=get_name(cls), annotation=cls)
    properties = get_schema_for_field_definition(field_definition, plugins=[PydanticSchemaPlugin()]).properties
    expected_foo_schema = Schema(type=OpenAPIType.INTEGER)
    expected_optional_foo_schema = Schema(one_of=[Schema(type=OpenAPIType.INTEGER), Schema(type=OpenAPIType.NULL)])

    assert properties
    assert properties["foo"] == expected_foo_schema
    assert properties["annotated_foo"] == expected_foo_schema
    assert properties["optional_foo"] == expected_optional_foo_schema


@pytest.mark.parametrize(
    "constrained",
    [
        pydantic_v1.constr(regex="^[a-zA-Z]$"),
        pydantic_v1.conlist(int, min_items=1),
        pydantic_v1.conset(int, min_items=1),
        pydantic_v1.conint(gt=10, lt=100),
        pydantic_v1.confloat(gt=10, lt=100),
        pydantic_v1.condecimal(gt=Decimal("10")),
        pydantic_v1.condate(gt=datetime.date.today()),
        pydantic_v2.constr(pattern="^[a-zA-Z]$"),
        pydantic_v2.conlist(int, min_length=1),
        pydantic_v2.conset(int, min_length=1),
        pydantic_v2.conint(gt=10, lt=100),
        pydantic_v2.confloat(ge=10, le=100),
        pydantic_v2.condecimal(gt=Decimal("10")),
        pydantic_v2.condate(gt=datetime.date.today()),
    ],
)
def test_is_pydantic_constrained_field(constrained: Any) -> None:
    PydanticSchemaPlugin.is_constrained_field(FieldDefinition.from_annotation(constrained))


def test_v2_constrained_secrets() -> None:
    # https://github.com/litestar-org/litestar/issues/3148
    class Model(pydantic_v2.BaseModel):
        string: pydantic_v2.SecretStr = pydantic_v2.Field(min_length=1)
        bytes_: pydantic_v2.SecretBytes = pydantic_v2.Field(min_length=1)

    schema = PydanticSchemaPlugin.for_pydantic_model(
        FieldDefinition.from_annotation(Model), schema_creator=SchemaCreator(plugins=[PydanticSchemaPlugin()])
    )
    assert schema.properties
    assert schema.properties["string"] == Schema(min_length=1, type=OpenAPIType.STRING)
    assert schema.properties["bytes_"] == Schema(min_length=1, type=OpenAPIType.STRING)


class V1ModelWithPrivateFields(pydantic_v1.BaseModel):
    class Config:
        underscore_fields_are_private = True

    _field: str = pydantic_v1.PrivateAttr()
    # include an invalid annotation here to ensure we never touch those fields
    _underscore_field: str = "foo"


class V1GenericModelWithPrivateFields(pydantic_v1.generics.GenericModel, Generic[T]):  # pyright: ignore
    class Config:
        underscore_fields_are_private = True

    _field: str = pydantic_v1.PrivateAttr()
    # include an invalid annotation here to ensure we never touch those fields
    _underscore_field: str = "foo"


class V2ModelWithPrivateFields(pydantic_v2.BaseModel):
    _field: str = pydantic_v2.PrivateAttr()
    # include an invalid annotation here to ensure we never touch those fields
    _underscore_field: str = "foo"


class V2GenericModelWithPrivateFields(pydantic_v2.BaseModel, Generic[T]):
    _field: str = pydantic_v2.PrivateAttr()
    # include an invalid annotation here to ensure we never touch those fields
    _underscore_field: str = "foo"


@pytest.mark.parametrize(
    "model_class",
    [
        V1ModelWithPrivateFields,
        V1GenericModelWithPrivateFields,
        V2ModelWithPrivateFields,
        V2GenericModelWithPrivateFields,
    ],
)
def test_exclude_private_fields(model_class: type[Union[pydantic_v1.BaseModel, pydantic_v2.BaseModel]]) -> None:
    # https://github.com/litestar-org/litestar/issues/3150
    schema = PydanticSchemaPlugin.for_pydantic_model(
        FieldDefinition.from_annotation(model_class), schema_creator=SchemaCreator(plugins=[PydanticSchemaPlugin()])
    )
    assert not schema.properties


def test_v1_constrained_str_with_default_factory_does_not_generate_title() -> None:
    # https://github.com/litestar-org/litestar/issues/3710
    class Model(pydantic_v1.BaseModel):
        test_str: str = pydantic_v1.Field(default_factory=str, max_length=600)

    @post(path="/")
    async def test(data: Model) -> str:
        return "success"

    schema = Litestar(route_handlers=[test]).openapi_schema.to_schema()
    assert (
        "title"
        not in schema["components"]["schemas"][
            "test_v1_constrained_str_with_default_factory_does_not_generate_title.Model"
        ]["properties"]["test_str"]["oneOf"][1]
    )
