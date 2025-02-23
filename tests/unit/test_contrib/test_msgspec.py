from __future__ import annotations

import itertools
from dataclasses import replace
from typing import TYPE_CHECKING, Annotated
from unittest.mock import ANY

import pytest
from msgspec import Meta, Struct, field

from litestar import Litestar, post
from litestar.dto import DTOField, Mark, MsgspecDTO, dto_field
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.typing import FieldDefinition

if TYPE_CHECKING:
    from typing import Callable


@pytest.fixture
def expected_field_defs(int_factory: Callable[[], int]) -> list[DTOFieldDefinition]:
    return [
        DTOFieldDefinition.from_field_definition(
            field_definition=FieldDefinition.from_kwarg(
                annotation=int,
                name="a",
            ),
            model_name=ANY,
            default_factory=None,
            dto_field=DTOField(),
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    annotation=int,
                    name="b",
                ),
                model_name=ANY,
                default_factory=None,
                dto_field=DTOField(mark=Mark.READ_ONLY),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
            kwarg_definition=ANY,
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    annotation=int,
                    name="c",
                ),
                model_name=ANY,
                default_factory=None,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
            kwarg_definition=ANY,
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    annotation=int,
                    name="d",
                    default=1,
                ),
                model_name=ANY,
                default_factory=None,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
            kwarg_definition=ANY,
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    annotation=int,
                    name="e",
                ),
                model_name=ANY,
                default_factory=int_factory,
                dto_field=DTOField(),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
            kwarg_definition=ANY,
        ),
        replace(
            DTOFieldDefinition.from_field_definition(
                field_definition=FieldDefinition.from_kwarg(
                    annotation=str,
                    name="computed",
                ),
                model_name=ANY,
                default_factory=None,
                dto_field=DTOField(mark="read-only"),
            ),
            metadata=ANY,
            type_wrappers=ANY,
            raw=ANY,
            kwarg_definition=ANY,
        ),
    ]


def test_field_definition_generation(
    int_factory: Callable[[], int], expected_field_defs: list[DTOFieldDefinition]
) -> None:
    class TestStruct(Struct):
        a: int
        b: Annotated[int, Meta(extra=dto_field("read-only"))]
        c: Annotated[int, Meta(gt=1)]
        d: int = field(default=1)
        e: int = field(default_factory=int_factory)

        @property
        def computed(self) -> str:
            return "i am computed"

        @property
        def _private_computed(self) -> str:
            return ""

    field_defs = list(MsgspecDTO.generate_field_definitions(TestStruct))
    assert field_defs[0].model_name == "TestStruct"
    for field_def, exp in itertools.zip_longest(expected_field_defs, field_defs, fillvalue=None):
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


def test_tag_field_included_in_schema() -> None:
    # default tag field, default tag value
    class Model(Struct, tag=True):
        regular_field: str

    # default tag field, custom tag value
    class Model2(Struct, tag=2):
        regular_field: str

    # custom tag field, custom tag value
    class Model3(Struct, tag_field="foo", tag="bar"):
        regular_field: str

    @post("/1")
    def handler(data: Model) -> None:
        return None

    @post("/2")
    def handler_2(data: Model2) -> None:
        return None

    @post("/3")
    def handler_3(data: Model3) -> None:
        return None

    components = Litestar(
        [handler, handler_2, handler_3],
        signature_types=[Model, Model2, Model3],
    ).openapi_schema.components.to_schema()["schemas"]

    assert components["test_tag_field_included_in_schema.Model"] == {
        "properties": {
            "regular_field": {"type": "string"},
            "type": {"type": "string", "const": "Model"},
        },
        "type": "object",
        "required": ["regular_field", "type"],
        "title": "Model",
    }

    assert components["test_tag_field_included_in_schema.Model2"] == {
        "properties": {
            "regular_field": {"type": "string"},
            "type": {"type": "integer", "const": 2},
        },
        "type": "object",
        "required": ["regular_field", "type"],
        "title": "Model2",
    }

    assert components["test_tag_field_included_in_schema.Model3"] == {
        "properties": {
            "regular_field": {"type": "string"},
            "foo": {"type": "string", "const": "bar"},
        },
        "type": "object",
        "required": ["foo", "regular_field"],
        "title": "Model3",
    }
