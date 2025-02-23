from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from typing import Annotated, ClassVar
from unittest.mock import ANY

import pytest

from litestar.dto import DataclassDTO, DTOField
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.typing import FieldDefinition


@dataclass
class Model:
    a: int
    b: str = field(default="b")
    c: list[int] = field(default_factory=list)
    d: ClassVar[float] = 1.0

    @property
    def computed(self) -> str:
        return "i am a property"


@pytest.fixture(name="dto_type")
def fx_dto_type() -> type[DataclassDTO[Model]]:
    return DataclassDTO[Model]


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
                    annotation=list[int],
                ),
                default_factory=list,
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
                    name="computed",
                    annotation=str,
                ),
                default_factory=None,
                model_name=Model.__name__,
                dto_field=DTOField(mark="read-only"),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
        ),
    ]
    for exp, field_def in itertools.zip_longest(expected, dto_type.generate_field_definitions(Model), fillvalue=None):
        assert exp == field_def


def test_dataclass_detect_nested(dto_type: type[DataclassDTO[Model]]) -> None:
    assert dto_type.detect_nested_field(FieldDefinition.from_annotation(Model)) is True
    assert dto_type.detect_nested_field(FieldDefinition.from_annotation(int)) is False


ReadOnlyInt = Annotated[int, DTOField("read-only")]


def test_dataclass_dto_annotated_dto_field() -> None:
    @dataclass
    class Model:
        a: Annotated[int, DTOField("read-only")]
        b: ReadOnlyInt

    dto_type = DataclassDTO[Model]
    fields = list(dto_type.generate_field_definitions(Model))
    assert fields[0].dto_field == DTOField("read-only")
    assert fields[1].dto_field == DTOField("read-only")


def test_property_underscore_exclude() -> None:
    @dataclass
    class Model:
        one: str

        @property
        def _computed(self) -> int:
            return 1

        @property
        def __also_computed(self) -> int:
            return 1

    dto_type = DataclassDTO[Model]
    fields = list(dto_type.generate_field_definitions(Model))
    assert fields[0].name == "one"
    assert len(fields) == 1
