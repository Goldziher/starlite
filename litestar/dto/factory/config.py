"""DTO domain types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import AbstractSet, Sequence

    from .types import FieldDefinition, FieldMappingType


__all__ = ("DTOConfig",)


@dataclass(frozen=True, eq=True)
class DTOConfig:
    """Control the generated DTO."""

    exclude: AbstractSet[str] = field(default_factory=set)
    """Explicitly exclude fields from the generated DTO, incompatible with ``include``."""
    include: AbstractSet[str] = field(default_factory=set)
    """Explicitly include fields on the generated DTO, incompatible with ``exclude``."""
    field_mapping: FieldMappingType = field(default_factory=dict)
    """Mapping of field names, to new name, or tuple of new name, new type."""
    field_definitions: Sequence[FieldDefinition] = field(default_factory=tuple)
    """Additional fields for data transfer."""
    max_nested_recursion: int = 0
    """The maximum number of times a self-referencing nested field should be followed."""
    max_nested_depth: int = 1
    """The maximum depth of nested items allowed for data transfer."""

    def __hash__(self) -> int:
        return hash(
            (
                tuple(self.exclude),
                tuple(self.include),
                tuple(self.field_mapping),
                self.field_definitions,
                self.max_nested_recursion,
                self.max_nested_depth,
            )
        )
