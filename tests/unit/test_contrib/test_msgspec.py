from __future__ import annotations

from typing import TYPE_CHECKING

from msgspec import Meta, Struct, field
from typing_extensions import Annotated

from litestar.dto import DTOField, MsgspecDTO, dto_field
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.typing import FieldDefinition

if TYPE_CHECKING:
    from typing import Callable


def test_field_definition_generation(
    int_factory: Callable[[], int], expected_field_defs: list[DTOFieldDefinition]
) -> None:
    class TestStruct(Struct):
        a: int
        b: Annotated[int, Meta(extra=dto_field("read-only"))]
        c: Annotated[int, Meta(gt=1)]
        d: int = field(default=1)
        e: int = field(default_factory=int_factory)

    field_defs = list(MsgspecDTO.generate_field_definitions(TestStruct))
    assert field_defs[0].model_name == "TestStruct"
    for field_def, exp in zip(field_defs, expected_field_defs):
        assert field_def == exp


def test_detect_nested_field() -> None:
    class TestStruct(Struct):
        a: int

    class NotStruct:
        pass

    assert MsgspecDTO.detect_nested_field(FieldDefinition.from_annotation(TestStruct)) is True
    assert MsgspecDTO.detect_nested_field(FieldDefinition.from_annotation(NotStruct)) is False


ReadOnlyInt = Annotated[int, DTOField("read-only")]


def test_msgspec_dto_annotated_dto_field() -> None:
    class Model(Struct):
        a: Annotated[int, DTOField("read-only")]
        b: ReadOnlyInt

    dto_type = MsgspecDTO[Model]
    fields = list(dto_type.generate_field_definitions(Model))
    assert fields[0].dto_field == DTOField("read-only")
    assert fields[1].dto_field == DTOField("read-only")
