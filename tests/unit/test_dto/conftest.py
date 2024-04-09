# ruff: noqa: UP006
from __future__ import annotations

from typing import Any, Collection, Generator, TypeVar, get_type_hints

import pytest

from litestar import Request, get
from litestar._openapi.schema_generation import SchemaCreator
from litestar.dto import AbstractDTO, DTOField, DTOFieldDefinition
from litestar.enums import MediaType
from litestar.openapi.spec import Reference, Schema
from litestar.testing import RequestFactory
from litestar.types.serialization import LitestarEncodableType
from litestar.typing import FieldDefinition

from . import Model

T = TypeVar("T", bound=Model)


@pytest.fixture
def ModelDataDTO() -> type[AbstractDTO]:
    class DTOCls(AbstractDTO[Model]):
        def decode_builtins(self, value: Any) -> Model:
            return Model(a=1, b="2")

        def decode_bytes(self, value: bytes) -> Model:
            return Model(a=1, b="2")

        def data_to_encodable_type(self, data: Model | Collection[Model]) -> bytes | LitestarEncodableType:
            return Model(a=1, b="2")

        @classmethod
        def create_openapi_schema(
            cls, field_definition: FieldDefinition, handler_id: str, schema_creator: SchemaCreator
        ) -> Reference | Schema:
            return Schema()

        @classmethod
        def generate_field_definitions(cls, model_type: type[Any]) -> Generator[DTOFieldDefinition, None, None]:
            for k, v in get_type_hints(model_type).items():
                yield DTOFieldDefinition.from_field_definition(
                    field_definition=FieldDefinition.from_kwarg(annotation=v, name=k),
                    model_name="Model",
                    default_factory=None,
                    dto_field=DTOField(),
                )

        @classmethod
        def detect_nested_field(cls, field_definition: FieldDefinition) -> bool:
            return False

    return DTOCls


@pytest.fixture()
def ModelReturnDTO() -> type[AbstractDTO]:
    class ReturnDO(AbstractDTO[Model]):
        def decode_builtins(self, value: Any) -> Any:
            raise RuntimeError("Return DTO should not have this method called")

        def decode_bytes(self, value: Any) -> Any:
            raise RuntimeError("Return DTO should not have this method called")

        def data_to_encodable_type(self, data: Model | Collection[Model]) -> bytes | LitestarEncodableType:
            return b'{"a": 1, "b": "2"}'

        @classmethod
        def create_openapi_schema(
            cls, field_definition: FieldDefinition, handler_id: str, schema_creator: SchemaCreator
        ) -> Reference | Schema:
            return Schema()

        @classmethod
        def generate_field_definitions(cls, model_type: type[Any]) -> Generator[DTOFieldDefinition, None, None]:
            for k, v in get_type_hints(model_type).items():
                yield DTOFieldDefinition.from_field_definition(
                    field_definition=FieldDefinition.from_kwarg(annotation=v, name=k),
                    model_name="Model",
                    default_factory=None,
                    dto_field=DTOField(),
                )

        @classmethod
        def detect_nested_field(cls, field_definition: FieldDefinition) -> bool:
            return False

    return ReturnDO


@pytest.fixture()
def asgi_connection() -> Request[Any, Any, Any]:
    @get("/", name="handler_id", media_type=MediaType.JSON)
    def _handler() -> None: ...

    return RequestFactory().get(path="/", route_handler=_handler)
