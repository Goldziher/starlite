from __future__ import annotations

from typing import TYPE_CHECKING, Generic, List, TypeVar
from unittest.mock import MagicMock

import pytest
from typing_extensions import Annotated, get_args, get_origin

from litestar import post
from litestar.dto.factory.config import DTOConfig
from litestar.dto.factory.exc import InvalidAnnotation
from litestar.dto.factory.stdlib.dataclass import DataclassDTO, DataT
from litestar.dto.factory.types import FieldDefinition
from litestar.types.empty import Empty
from litestar.utils.signature import ParsedType

from . import Model

if TYPE_CHECKING:
    from pytest import MonkeyPatch

    from litestar.testing import RequestFactory


def test_on_registration(monkeypatch: MonkeyPatch) -> None:
    dto_type = DataclassDTO[Model]
    postponed_cls_init_mock = MagicMock()
    monkeypatch.setattr(dto_type, "postponed_cls_init", postponed_cls_init_mock)
    # call startup twice
    dto_type.on_registration(ParsedType(Model), post())
    dto_type.on_registration(ParsedType(Model), post())
    assert postponed_cls_init_mock.called_once()


def test_forward_referenced_type_argument_raises_exception() -> None:
    with pytest.raises(InvalidAnnotation):
        DataclassDTO["Model"]


def test_type_narrowing_with_scalar_type_arg() -> None:
    dto = DataclassDTO[Model]
    assert dto.configs == (DTOConfig(),)
    assert dto._postponed_cls_init_called is False
    assert dto.annotation is Model
    assert dto.model_type is Model


def test_type_narrowing_with_iterable_type_arg() -> None:
    dto = DataclassDTO[List[Model]]
    assert dto.configs == (DTOConfig(),)
    assert dto._postponed_cls_init_called is False
    assert get_origin(dto.annotation) is list
    assert get_args(dto.annotation) == (Model,)
    assert dto.model_type is Model


def test_type_narrowing_with_annotated_scalar_type_arg() -> None:
    config = DTOConfig()
    dto = DataclassDTO[Annotated[Model, config]]
    assert dto.configs[0] is config
    assert dto._postponed_cls_init_called is False
    assert dto.annotation is Model
    assert dto.model_type is Model


def test_type_narrowing_with_annotated_iterable_type_arg() -> None:
    config = DTOConfig()
    dto = DataclassDTO[Annotated[List[Model], config]]
    assert dto.configs[0] is config
    assert dto._postponed_cls_init_called is False
    assert get_origin(dto.annotation) is list
    assert get_args(dto.annotation) == (Model,)
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
    assert generic_dto.configs[0] is config
    assert not hasattr(generic_dto, "annotation")
    assert not hasattr(generic_dto, "model_type")


def test_extra_annotated_metadata_ignored() -> None:
    config = DTOConfig()
    dto = DataclassDTO[Annotated[Model, config, "a"]]
    assert dto.configs[0] is config


def test_config_provided_by_subclass() -> None:
    dto_config = DTOConfig()

    class DTOWithConfig(DataclassDTO[DataT], Generic[DataT]):
        config = dto_config

    dto = DTOWithConfig[Model]
    assert dto.config is dto_config


def test_overwrite_config() -> None:
    t = TypeVar("t", bound=Model)
    generic_dto = DataclassDTO[Annotated[t, DTOConfig()]]
    config = DTOConfig()
    dto = generic_dto[Annotated[Model, config]]  # pyright: ignore
    assert dto.configs[0] is config


async def test_from_connection(request_factory: RequestFactory) -> None:
    dto_type = DataclassDTO[Model]
    dto_type.postponed_cls_init()
    dto_instance = await dto_type.from_connection(request_factory.post(data={"a": 1, "b": "two"}))
    assert dto_instance.data == Model(a=1, b="two")


def test_config_field_definitions() -> None:
    new_def = FieldDefinition(name="z", parsed_type=ParsedType(str), default="something")
    config = DTOConfig(field_definitions=[new_def])
    dto_type = DataclassDTO[Annotated[Model, config]]
    dto_type.postponed_cls_init()
    assert dto_type.field_definitions["z"] is new_def


def test_config_field_mapping() -> None:
    config = DTOConfig(field_mapping={"a": "z"})
    dto_type = DataclassDTO[Annotated[Model, config]]
    dto_type.postponed_cls_init()
    assert "a" not in dto_type.field_definitions
    assert "z" in dto_type.field_definitions


def test_config_field_mapping_new_definition() -> None:
    config = DTOConfig(field_mapping={"a": FieldDefinition(name="z", parsed_type=ParsedType(str), default=Empty)})
    dto_type = DataclassDTO[Annotated[Model, config]]
    dto_type.postponed_cls_init()
    assert "a" not in dto_type.field_definitions
    z = dto_type.field_definitions["z"]
    assert isinstance(z, FieldDefinition)
    assert z.name == "z"
    assert z.annotation is str


def test_type_narrowing_with_multiple_configs() -> None:
    config_1 = DTOConfig()
    config_2 = DTOConfig()
    dto = DataclassDTO[Annotated[Model, config_1, config_2]]
    assert len(dto.configs) == 2
    assert dto.configs[0] is config_1
    assert dto.configs[1] is config_2
