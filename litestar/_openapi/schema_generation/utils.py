from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar.utils.helpers import get_name

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from litestar.openapi.spec import Example
    from litestar.typing import FieldDefinition

__all__ = ("_should_create_literal_schema",)


def _should_create_literal_schema(field_definition: FieldDefinition) -> bool:
    """Predicate to determine if we should create a literal schema for the field def, or not.

    This returns ``True`` if the field definition is an literal, or if the field definition is a union
    of a literal and None.

    When an annotation is `Literal["anything"] | None` we should create a schema for the literal that includes `null`
    in the enum values.

    Args:
        field_definition: A field definition instance.

    Returns:
        A boolean
    """
    return field_definition.is_literal or (
        field_definition.is_optional
        and all(inner.is_literal for inner in field_definition.inner_types if not inner.is_none_type)
    )


def get_formatted_examples(field_definition: FieldDefinition, examples: Sequence[Example]) -> Mapping[str, Example]:
    """Format the examples into the OpenAPI schema format."""

    name = field_definition.name or get_name(field_definition.type_)
    name = name.lower()

    return {f"{name}-example-{i}": example for i, example in enumerate(examples, 1)}


def get_json_schema_formatted_examples(examples: Sequence[Example]) -> list[Any]:
    """Format the examples into the JSON schema format."""
    return [example.value for example in examples]
