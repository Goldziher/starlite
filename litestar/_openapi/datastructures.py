from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING, _GenericAlias  # type: ignore[attr-defined]

from litestar.exceptions import ImproperlyConfiguredException
from litestar.openapi.spec import Reference, Schema
from litestar.params import KwargDefinition

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from litestar.openapi import OpenAPIConfig
    from litestar.plugins import OpenAPISchemaPluginProtocol
    from litestar.typing import FieldDefinition


INVALID_KEY_CHARACTER_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


def _longest_common_prefix(tuples_: list[tuple[str, ...]]) -> tuple[str, ...]:
    """Find the longest common prefix of a list of tuples.

    Args:
        tuples_: A list of tuples to find the longest common prefix of.

    Returns:
        The longest common prefix of the tuples.
    """
    prefix_ = tuples_[0]
    for t in tuples_:
        # Compare the current prefix with each tuple and shorten it
        prefix_ = prefix_[: min(len(prefix_), len(t))]
        for i in range(len(prefix_)):
            if prefix_[i] != t[i]:
                prefix_ = prefix_[:i]
                break
    return prefix_


def _get_component_key_override(field: FieldDefinition) -> str | None:
    if (
        (kwarg_definition := field.kwarg_definition)
        and isinstance(kwarg_definition, KwargDefinition)
        and (schema_key := kwarg_definition.schema_component_key)
    ):
        return schema_key
    return None


def _get_normalized_schema_key(field_definition: FieldDefinition) -> tuple[str, ...]:
    """Create a key for a type annotation.

    The key should be a tuple such as ``("path", "to", "type", "TypeName")``.

    Args:
        field_definition: Field definition

    Returns:
        A tuple of strings.
    """
    if override := _get_component_key_override(field_definition):
        return (override,)

    annotation = field_definition.annotation
    module = getattr(annotation, "__module__", "")
    name = str(annotation)[len(module) + 1 :] if isinstance(annotation, _GenericAlias) else annotation.__qualname__
    name = name.replace(".<locals>.", ".")
    return *module.split("."), re.sub(INVALID_KEY_CHARACTER_PATTERN, "_", name)


class RegisteredSchema:
    """Object to store a schema and any references to it."""

    def __init__(self, key: tuple[str, ...], schema: Schema, references: list[Reference]) -> None:
        """Create a new RegisteredSchema object.

        Args:
            key: The key used to register the schema.
            schema: The schema object.
            references: A list of references to the schema.
        """
        self.key = key
        self.schema = schema
        self.references = references


class SchemaRegistry:
    """A registry for object schemas.

    This class is used to store schemas that we reference from other parts of the spec.

    Its main purpose is to allow us to generate the components/schemas section of the spec once we have
    collected all the schemas that should be included.

    This allows us to determine a path to the schema in the components/schemas section of the spec that
    is unique and as short as possible.
    """

    def __init__(self) -> None:
        self._schema_key_map: dict[tuple[str, ...], RegisteredSchema] = {}
        self._schema_reference_map: dict[int, RegisteredSchema] = {}
        self._model_name_groups: defaultdict[str, list[RegisteredSchema]] = defaultdict(list)
        self._component_type_map: dict[tuple[str, ...], FieldDefinition] = {}

    def get_schema_for_field_definition(self, field: FieldDefinition) -> Schema:
        """Get a registered schema by its key.

        Args:
            field: The field definition to get the schema for

        Returns:
            A RegisteredSchema object.
        """
        key = _get_normalized_schema_key(field)
        if key not in self._schema_key_map:
            self._schema_key_map[key] = registered_schema = RegisteredSchema(key, Schema(), [])
            self._model_name_groups[key[-1]].append(registered_schema)
            self._component_type_map[key] = field
        else:
            if (existing_type := self._component_type_map[key]) != field:
                raise ImproperlyConfiguredException(
                    f"Schema component keys must be unique. Cannot override existing key {'_'.join(key)!r} for type "
                    f"{existing_type.raw!r} with new type {field.raw!r}"
                )
        return self._schema_key_map[key].schema

    def get_reference_for_field_definition(self, field: FieldDefinition) -> Reference | None:
        """Get a reference to a registered schema by its key.

        Args:
            field: The field definition to get the reference for

        Returns:
            A Reference object.
        """
        key = _get_normalized_schema_key(field)
        if key not in self._schema_key_map:
            return None

        if (existing_type := self._component_type_map[key]) != field:
            # TODO: This should check for strict equality, e.g. changes in type metadata
            # However, this is currently not possible to do without breaking things, as
            # we allow to define metadata on a type annotation in one place to be used
            # for the same type in a different place, where that same type is *not*
            # annotated with this metadata. The proper fix for this would be to e.g.
            # inline DTO definitions when they are created at the handler level, as
            # they won't be reused (they already generate a unique key), and create a
            # more strict lookup policy for component schemas
            msg = (
                f"Schema component keys must be unique. While obtaining a reference for the type '{field.raw!r}', the "
                f"generated key {'_'.join(key)!r} was already associated with a different type '{existing_type.raw!r}'. "
            )
            if key_override := _get_component_key_override(field):  # pragma: no branch
                # Currently, this can never not be true, however, in the future we might
                # decide to do a stricter equality check as lined out above, in which
                # case there can be other cases than overrides that cause this error
                msg += f"Hint: Both types are defining a 'schema_component_key' with the value of {key_override!r}"
            raise ImproperlyConfiguredException(msg)

        registered_schema = self._schema_key_map[key]
        reference = Reference(f"#/components/schemas/{'_'.join(key)}")
        registered_schema.references.append(reference)
        self._schema_reference_map[id(reference)] = registered_schema
        return reference

    def from_reference(self, reference: Reference) -> RegisteredSchema:
        """Get a registered schema by its reference.

        Args:
            reference: The reference to the schema to get.

        Returns:
            A RegisteredSchema object.
        """
        return self._schema_reference_map[id(reference)]

    def __iter__(self) -> Iterator[RegisteredSchema]:
        """Iterate over the registered schemas."""
        return iter(self._schema_key_map.values())

    @staticmethod
    def set_reference_paths(name: str, registered_schema: RegisteredSchema) -> None:
        """Set the reference paths for a registered schema."""
        for reference in registered_schema.references:
            reference.ref = f"#/components/schemas/{name}"

    @staticmethod
    def remove_common_prefix(tuples: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
        """Remove the common prefix from a list of tuples.

        Args:
            tuples: A list of tuples to remove the common prefix from.

        Returns:
            A list of tuples with the common prefix removed.
        """

        prefix = _longest_common_prefix(tuples)
        prefix_length = len(prefix)
        return [t[prefix_length:] for t in tuples]

    def generate_components_schemas(self) -> dict[str, Schema]:
        """Generate the components/schemas section of the spec.

        Returns:
            A dictionary of schemas.
        """
        components_schemas: dict[str, Schema] = {}

        for name, name_group in self._model_name_groups.items():
            if len(name_group) == 1:
                self.set_reference_paths(name, name_group[0])
                components_schemas[name] = name_group[0].schema
                continue

            full_keys = [registered_schema.key for registered_schema in name_group]
            names = ["_".join(k) for k in self.remove_common_prefix(full_keys)]
            for name_, registered_schema in zip(names, name_group):
                self.set_reference_paths(name_, registered_schema)
                components_schemas[name_] = registered_schema.schema

        # Sort them by name to ensure they're always generated in the same order.
        return {name: components_schemas[name] for name in sorted(components_schemas.keys())}


class OpenAPIContext:
    def __init__(
        self,
        openapi_config: OpenAPIConfig,
        plugins: Sequence[OpenAPISchemaPluginProtocol],
    ) -> None:
        self.openapi_config = openapi_config
        self.plugins = plugins
        self.operation_ids: set[str] = set()
        self.schema_registry = SchemaRegistry()

    def add_operation_id(self, operation_id: str) -> None:
        """Add an operation ID to the context.

        Args:
            operation_id: Operation ID to add.
        """
        if operation_id in self.operation_ids:
            raise ImproperlyConfiguredException(
                "operation_ids must be unique, "
                f"please ensure the value of 'operation_id' is either not set or unique for {operation_id!r}"
            )
        self.operation_ids.add(operation_id)
