from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from typing import ClassVar, List
from unittest.mock import ANY

import pytest
from typing_extensions import Annotated

from litestar.dto import DataclassDTO, DTOField
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.typing import FieldDefinition


@dataclass
class Model:
    a: int
    b: str = field(default="b")
    c: List[int] = field(default_factory=list)  # noqa: UP006
    d: ClassVar[float] = 1.0


@pytest.fixture(name="dto_type")
def fx_dto_type() -> type[DataclassDTO[Model]]:
    return DataclassDTO[Model]


@pytest.mark.skipif(sys.version_info >= (3, 9), reason="generic builtin collection")
def test_dataclass_field_definitions_38(dto_type: type[DataclassDTO[Model]]) -> None:
    expected = [
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    name="a",
                    annotation=int,
                ),
                default_factory=None,
                model_name=Model.__name__,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(name="b", annotation=str, default="b"),
                default_factory=None,
                model_name=Model.__name__,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    name="c",
                    annotation=List[int],
                ),
                default_factory=list,
                model_name=Model.__name__,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
        ),
    ]
    for field_def, exp in zip(dto_type.generate_field_definitions(Model), expected):
        assert field_def == exp


def test_dataclass_field_definitions(dto_type: type[DataclassDTO[Model]]) -> None:
    expected = [
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    name="a",
                    annotation=int,
                ),
                default_factory=None,
                model_name=Model.__name__,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(name="b", annotation=str, default="b"),
                default_factory=None,
                model_name=Model.__name__,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    name="c",
                    annotation=List[int],
                ),
                default_factory=list,
                model_name=Model.__name__,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
        ),
    ]
    for field_def, exp in zip(dto_type.generate_field_definitions(Model), expected):
        assert field_def == exp


def test_dataclass_detect_nested(dto_type: type[DataclassDTO[Model]]) -> None:
    assert dto_type.detect_nested_field(FieldDefinition.from_annotation(Model)) is True
    assert dto_type.detect_nested_field(FieldDefinition.from_annotation(int)) is False


ReadOnlyInt = Annotated[int, DTOField("read-only")]


def test_dataclass_dto_annotated_dto_field() -> None:
    Annotated[int, DTOField("read-only")]

    @dataclass
    class Model:
        a: Annotated[int, DTOField("read-only")]
        b: ReadOnlyInt

    dto_type = DataclassDTO[Model]
    fields = list(dto_type.generate_field_definitions(Model))
    assert fields[0].dto_field == DTOField("read-only")
    assert fields[1].dto_field == DTOField("read-only")
