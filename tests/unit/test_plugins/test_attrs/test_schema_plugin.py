from typing import Annotated, Generic, Optional, TypeVar

from attrs import define

from litestar.openapi.spec import OpenAPIType
from litestar.openapi.spec.schema import Schema
from litestar.plugins.attrs import AttrsSchemaPlugin
from litestar.typing import FieldDefinition
from litestar.utils.helpers import get_name
from tests.helpers import get_schema_for_field_definition

T = TypeVar("T")


@define
class AttrsGeneric(Generic[T]):
    foo: T
    optional_foo: Optional[T]
    annotated_foo: Annotated[T, object()]


def test_schema_generation_with_generic_classes() -> None:
    cls = AttrsGeneric[int]
    expected_foo_schema = Schema(type=OpenAPIType.INTEGER)
    expected_optional_foo_schema = Schema(one_of=[Schema(type=OpenAPIType.INTEGER), Schema(type=OpenAPIType.NULL)])

    field_definition = FieldDefinition.from_kwarg(name=get_name(cls), annotation=cls)
    properties = get_schema_for_field_definition(field_definition, plugins=[AttrsSchemaPlugin()]).properties

    assert properties
    assert properties["foo"] == expected_foo_schema
    assert properties["annotated_foo"] == expected_foo_schema
    assert properties["optional_foo"] == expected_optional_foo_schema
