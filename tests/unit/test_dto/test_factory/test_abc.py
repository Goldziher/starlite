# ruff: noqa: UP006
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple, TypeVar, Union
from unittest.mock import patch

import pytest
from typing_extensions import Annotated

from litestar._openapi.schema_generation import SchemaCreator
from litestar.dto import DataclassDTO, DTOConfig
from litestar.dto.interface import ConnectionContext, HandlerContext
from litestar.enums import RequestEncodingType
from litestar.exceptions.dto_exceptions import InvalidAnnotationException
from litestar.serialization import default_deserializer
from litestar.typing import FieldDefinition

from . import Model

if TYPE_CHECKING:
    from typing import Any

    from pytest import MonkeyPatch

    from litestar.dto._backend import DTOBackend
    from litestar.testing import RequestFactory

T = TypeVar("T", bound=Model)


def get_backend(dto_type: type[DataclassDTO[Any]]) -> DTOBackend:
    return next(iter(dto_type._type_backend_map.values()))


def test_forward_referenced_type_argument_raises_exception() -> None:
    with pytest.raises(InvalidAnnotationException):
        DataclassDTO["Model"]


def test_union_type_argument_raises_exception() -> None:
    class ModelB(Model):
        ...

    with pytest.raises(InvalidAnnotationException):
        DataclassDTO[Union[Model, ModelB]]


def test_type_narrowing_with_scalar_type_arg() -> None:
    dto = DataclassDTO[Model]
    assert dto.config == DTOConfig()
    assert dto.model_type is Model


def test_type_narrowing_with_annotated_scalar_type_arg() -> None:
    config = DTOConfig()
    dto = DataclassDTO[Annotated[Model, config]]
    assert dto.config is config
    assert dto.model_type is Model


def test_type_narrowing_with_only_type_var() -> None:
    t = TypeVar("t", bound=Model)
    generic_dto = DataclassDTO[t]
    assert generic_dto is DataclassDTO


def test_type_narrowing_with_annotated_type_var() -> None:
    config = DTOConfig()
    t = TypeVar("t", bound=Model)
    generic_dto = DataclassDTO[Annotated[t, config]]
    assert generic_dto is not DataclassDTO
    assert issubclass(generic_dto, DataclassDTO)
    assert generic_dto.config is config
    assert not hasattr(generic_dto, "model_type")


def test_extra_annotated_metadata_ignored() -> None:
    config = DTOConfig()
    dto = DataclassDTO[Annotated[Model, config, "a"]]
    assert dto.config is config


def test_overwrite_config() -> None:
    first = DTOConfig(exclude={"a"})
    generic_dto = DataclassDTO[Annotated[T, first]]
    second = DTOConfig(exclude={"b"})
    dto = generic_dto[Annotated[Model, second]]  # pyright: ignore
    assert dto.config is second


def test_existing_config_not_overwritten() -> None:
    assert getattr(DataclassDTO, "_config", None) is None
    first = DTOConfig(exclude={"a"})
    generic_dto = DataclassDTO[Annotated[T, first]]
    dto = generic_dto[Model]  # pyright: ignore
    assert dto.config is first


def test_config_assigned_via_subclassing() -> None:
    class CustomGenericDTO(DataclassDTO[T]):
        config = DTOConfig(exclude={"a"})

    concrete_dto = CustomGenericDTO[Model]

    assert concrete_dto.config.exclude == {"a"}


async def test_from_bytes(request_factory: RequestFactory) -> None:
    dto_type = DataclassDTO[Model]
    dto_type.on_registration(
        HandlerContext(handler_id="handler", dto_for="data", field_definition=FieldDefinition.from_annotation(Model))
    )
    conn_ctx = ConnectionContext(
        handler_id="handler",
        request_encoding_type=RequestEncodingType.JSON,
        default_deserializer=default_deserializer,
        type_decoders=None,
    )
    assert dto_type(conn_ctx).bytes_to_data_type(b'{"a":1,"b":"two"}') == Model(a=1, b="two")


def test_config_field_rename() -> None:
    config = DTOConfig(rename_fields={"a": "z"})
    dto_type = DataclassDTO[Annotated[Model, config]]
    dto_type.on_registration(
        HandlerContext(handler_id="handler", dto_for="data", field_definition=FieldDefinition.from_annotation(Model))
    )
    field_definitions = get_backend(dto_type).parsed_field_definitions
    assert field_definitions[0].serialization_name == "z"


def test_type_narrowing_with_multiple_configs() -> None:
    config_1 = DTOConfig()
    config_2 = DTOConfig()
    dto = DataclassDTO[Annotated[Model, config_1, config_2]]
    assert dto.config is config_1


def test_raises_invalid_annotation_for_non_homogenous_collection_types() -> None:
    dto_type = DataclassDTO[Model]

    with pytest.raises(InvalidAnnotationException):
        dto_type.on_registration(
            HandlerContext(
                handler_id="handler",
                dto_for="data",
                field_definition=FieldDefinition.from_annotation(Tuple[Model, str]),
            )
        )


def test_raises_invalid_annotation_for_mismatched_types() -> None:
    dto_type = DataclassDTO[Model]

    @dataclass
    class OtherModel:
        a: int

    with pytest.raises(InvalidAnnotationException):
        dto_type.on_registration(
            HandlerContext(
                handler_id="handler", dto_for="data", field_definition=FieldDefinition.from_annotation(OtherModel)
            )
        )


def test_sub_types_supported() -> None:
    dto_type = DataclassDTO[Model]

    @dataclass
    class SubType(Model):
        c: int

    dto_type.on_registration(
        HandlerContext(handler_id="handler", dto_for="data", field_definition=FieldDefinition.from_annotation(SubType))
    )
    assert dto_type._handler_backend_map[("data", "handler")].parsed_field_definitions[-1].name == "c"


def test_create_openapi_schema(monkeypatch: MonkeyPatch) -> None:
    dto_type = DataclassDTO[Model]
    dto_type.on_registration(
        HandlerContext(handler_id="handler", dto_for="data", field_definition=FieldDefinition.from_annotation(Model))
    )

    with patch("litestar.dto._backend.DTOBackend.create_openapi_schema") as mock:
        schema_creator = SchemaCreator()
        dto_type.create_openapi_schema("data", "handler", schema_creator)
        mock.assert_called_once_with(schema_creator)
