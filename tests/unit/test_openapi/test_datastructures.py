from __future__ import annotations

from typing import Generic, TypeVar

import msgspec
import pytest

from litestar._openapi.datastructures import SchemaRegistry, _get_normalized_schema_key
from litestar.exceptions import ImproperlyConfiguredException
from litestar.openapi.spec import Reference, Schema
from litestar.params import KwargDefinition
from litestar.typing import FieldDefinition
from tests.models import DataclassPerson


@pytest.fixture()
def schema_registry() -> SchemaRegistry:
    return SchemaRegistry()


def test_get_schema_for_field_definition(schema_registry: SchemaRegistry) -> None:
    assert not schema_registry._schema_key_map
    assert not schema_registry._schema_reference_map
    assert not schema_registry._model_name_groups
    field = FieldDefinition.from_annotation(str)
    schema = schema_registry.get_schema_for_field_definition(field)
    key = _get_normalized_schema_key(field)
    assert isinstance(schema, Schema)
    assert key in schema_registry._schema_key_map
    assert not schema_registry._schema_reference_map
    assert len(schema_registry._model_name_groups[key[-1]]) == 1
    assert schema_registry._model_name_groups[key[-1]][0].schema is schema
    assert schema_registry.get_schema_for_field_definition(field) is schema


def test_get_reference_for_field_definition(schema_registry: SchemaRegistry) -> None:
    assert not schema_registry._schema_key_map
    assert not schema_registry._schema_reference_map
    assert not schema_registry._model_name_groups
    field = FieldDefinition.from_annotation(str)
    key = _get_normalized_schema_key(field)

    assert schema_registry.get_reference_for_field_definition(field) is None
    schema_registry.get_schema_for_field_definition(field)
    reference = schema_registry.get_reference_for_field_definition(field)
    assert isinstance(reference, Reference)
    assert id(reference) in schema_registry._schema_reference_map
    assert reference in schema_registry._schema_key_map[key].references


def test_get_normalized_schema_key() -> None:
    class LocalClass(msgspec.Struct):
        id: str

    T = TypeVar("T")

    # replace each of the long strings with underscores with a tuple of strings split at each underscore
    assert _get_normalized_schema_key(FieldDefinition.from_annotation(LocalClass)) == (
        "tests",
        "unit",
        "test_openapi",
        "test_datastructures",
        "test_get_normalized_schema_key.LocalClass",
    )

    assert _get_normalized_schema_key(FieldDefinition.from_annotation(DataclassPerson)) == (
        "tests",
        "models",
        "DataclassPerson",
    )

    builtin_dict = dict[str, list[int]]
    assert _get_normalized_schema_key(FieldDefinition.from_annotation(builtin_dict)) == (
        "builtins",
        "dict",
    )

    builtin_with_custom = dict[str, DataclassPerson]
    assert _get_normalized_schema_key(FieldDefinition.from_annotation(builtin_with_custom)) == (
        "builtins",
        "dict",
    )

    class LocalGeneric(Generic[T]):
        pass

    assert _get_normalized_schema_key(FieldDefinition.from_annotation(LocalGeneric)) == (
        "tests",
        "unit",
        "test_openapi",
        "test_datastructures",
        "test_get_normalized_schema_key.LocalGeneric",
    )

    generic_int = LocalGeneric[int]
    generic_str = LocalGeneric[str]

    assert _get_normalized_schema_key(FieldDefinition.from_annotation(generic_int)) == (
        "tests",
        "unit",
        "test_openapi",
        "test_datastructures",
        "test_get_normalized_schema_key.LocalGeneric_int_",
    )

    assert _get_normalized_schema_key(FieldDefinition.from_annotation(generic_str)) == (
        "tests",
        "unit",
        "test_openapi",
        "test_datastructures",
        "test_get_normalized_schema_key.LocalGeneric_str_",
    )

    assert _get_normalized_schema_key(FieldDefinition.from_annotation(generic_int)) != _get_normalized_schema_key(
        FieldDefinition.from_annotation(generic_str)
    )


def test_raise_on_override_for_same_field_definition() -> None:
    registry = SchemaRegistry()
    schema = registry.get_schema_for_field_definition(
        FieldDefinition.from_annotation(str, kwarg_definition=KwargDefinition(schema_component_key="foo"))
    )
    # registering the same thing again with the same name should work
    assert (
        registry.get_schema_for_field_definition(
            FieldDefinition.from_annotation(str, kwarg_definition=KwargDefinition(schema_component_key="foo"))
        )
        is schema
    )
    # registering the same *type* with a different name should result in a different schema
    assert (
        registry.get_schema_for_field_definition(
            FieldDefinition.from_annotation(str, kwarg_definition=KwargDefinition(schema_component_key="bar"))
        )
        is not schema
    )
    # registering a different type with a previously used name should raise an exception
    with pytest.raises(ImproperlyConfiguredException):
        registry.get_schema_for_field_definition(
            FieldDefinition.from_annotation(int, kwarg_definition=KwargDefinition(schema_component_key="foo"))
        )
