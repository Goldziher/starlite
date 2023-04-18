from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import pytest
from typing_extensions import Annotated

from litestar import post
from litestar.dto.factory.backends import PydanticDTOBackend
from litestar.dto.factory.config import DTOConfig
from litestar.dto.factory.exc import InvalidAnnotation
from litestar.dto.factory.stdlib.dataclass import DataclassDTO
from litestar.dto.factory.types import FieldDefinition
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.types.empty import Empty
from litestar.utils.signature import ParsedType

from . import Model

if TYPE_CHECKING:
    from typing import Any

    from litestar.connection import Request
    from litestar.dto.factory.backends.abc import AbstractDTOBackend
    from litestar.handlers.http_handlers import HTTPRouteHandler
    from litestar.testing import RequestFactory


def make_connection(
    request_factory: RequestFactory, handler: HTTPRouteHandler, **kwargs: Any
) -> Request[Any, Any, Any]:
    connection = request_factory.post(**kwargs)
    connection.scope["route_handler"] = handler
    return connection


def get_backend(dto_type: type[DataclassDTO[Any]]) -> AbstractDTOBackend:
    return next(iter(dto_type._type_backend_map.values()))


def test_forward_referenced_type_argument_raises_exception() -> None:
    with pytest.raises(InvalidAnnotation):
        DataclassDTO["Model"]


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
    t = TypeVar("t", bound=Model)
    first = DTOConfig(exclude={"a"})
    generic_dto = DataclassDTO[Annotated[t, first]]
    second = DTOConfig(exclude={"b"})
    dto = generic_dto[Annotated[Model, second]]  # pyright: ignore
    assert dto.config is second


async def test_from_bytes(request_factory: RequestFactory) -> None:
    @post()
    def handler(data: Model) -> Model:
        return data

    dto_type = DataclassDTO[Model]
    dto_type.on_registration(handler, "data")
    connection = make_connection(request_factory, handler, data={"a": 1, "b": "two"})
    assert dto_type(connection).bytes_to_data_type(b'{"a":1,"b":"two"}') == Model(a=1, b="two")


def test_config_field_definitions() -> None:
    @post()
    def handler(data: Model) -> Model:
        return data

    new_def = FieldDefinition(name="z", parsed_type=ParsedType(str), default="something")
    config = DTOConfig(field_definitions=(new_def,))
    dto_type = DataclassDTO[Annotated[Model, config]]
    dto_type.on_registration(handler, "data")
    assert get_backend(dto_type).field_definitions["z"] is new_def


def test_config_field_mapping() -> None:
    @post()
    def handler(data: Model) -> Model:
        return data

    config = DTOConfig(field_mapping={"a": "z"})
    dto_type = DataclassDTO[Annotated[Model, config]]
    dto_type.on_registration(handler, "data")
    field_definitions = get_backend(dto_type).field_definitions
    assert "a" not in field_definitions
    assert "z" in field_definitions


def test_config_field_mapping_new_definition() -> None:
    @post()
    def handler(data: Model) -> Model:
        return data

    config = DTOConfig(field_mapping={"a": FieldDefinition(name="z", parsed_type=ParsedType(str), default=Empty)})
    dto_type = DataclassDTO[Annotated[Model, config]]
    dto_type.on_registration(handler, "data")
    field_definitions = get_backend(dto_type).field_definitions
    assert "a" not in field_definitions
    z = field_definitions["z"]
    assert isinstance(z, FieldDefinition)
    assert z.name == "z"
    assert z.annotation is str


def test_type_narrowing_with_multiple_configs() -> None:
    config_1 = DTOConfig()
    config_2 = DTOConfig()
    dto = DataclassDTO[Annotated[Model, config_1, config_2]]
    assert dto.config is config_1


def test_url_encoded_data_uses_pydantic_backend() -> None:
    @post()
    def handler_1(data: Model = Body(media_type=RequestEncodingType.URL_ENCODED)) -> Model:
        return data

    @post()
    def handler_2(data: Annotated[Model, Body(media_type=RequestEncodingType.URL_ENCODED)]) -> Model:
        return data

    for handler in handler_1, handler_2:
        dto_type = DataclassDTO[Model]
        dto_type.on_registration(handler, "data")
        assert isinstance(dto_type._handler_backend_map[("data", handler)], PydanticDTOBackend)
