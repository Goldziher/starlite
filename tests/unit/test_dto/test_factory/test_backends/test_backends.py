# ruff: noqa: UP006,UP007
from __future__ import annotations

from dataclasses import dataclass, field
from types import ModuleType
from typing import TYPE_CHECKING, Callable, List, Optional

import pytest
from msgspec import Struct, to_builtins

from litestar._openapi.schema_generation import SchemaCreator
from litestar.contrib.pydantic import PydanticInitPlugin
from litestar.dto import DataclassDTO, DTOConfig, DTOField
from litestar.dto._backend import BackendContext, DTOBackend
from litestar.dto._types import CollectionType, SimpleType, TransferDTOFieldDefinition
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.dto.interface import ConnectionContext
from litestar.enums import MediaType, RequestEncodingType
from litestar.exceptions import SerializationException
from litestar.openapi.spec.reference import Reference
from litestar.serialization import default_deserializer, encode_json
from litestar.typing import FieldDefinition

if TYPE_CHECKING:
    from typing import Any


@dataclass
class NestedDC:
    a: int
    b: str


@dataclass
class DC:
    a: int
    nested: NestedDC
    nested_list: List[NestedDC]
    b: str = field(default="b")
    c: List[int] = field(default_factory=list)
    optional: Optional[str] = None


DESTRUCTURED = {
    "a": 1,
    "b": "b",
    "c": [],
    "nested": {"a": 1, "b": "two"},
    "nested_list": [{"a": 1, "b": "two"}],
    "optional": None,
}
RAW = b'{"a":1,"nested":{"a":1,"b":"two"},"nested_list":[{"a":1,"b":"two"}],"b":"b","c":[],"optional":null}'
COLLECTION_RAW = (
    b'[{"a":1,"nested":{"a":1,"b":"two"},"nested_list":[{"a":1,"b":"two"}],"b":"b","c":[],"optional":null}]'
)
STRUCTURED = DC(a=1, b="b", c=[], nested=NestedDC(a=1, b="two"), nested_list=[NestedDC(a=1, b="two")], optional=None)


@pytest.fixture(name="backend_context")
def fx_backend_context() -> BackendContext:
    return BackendContext(
        dto_config=DTOConfig(),
        dto_for="data",
        field_definition=FieldDefinition.from_annotation(DC),
        field_definition_generator=DataclassDTO.generate_field_definitions,
        is_nested_field_predicate=DataclassDTO.detect_nested_field,
        model_type=DC,
        wrapper_attribute_name=None,
    )


def fx_backend(backend_context: BackendContext, request: Any) -> DTOBackend:
    return request.param(backend_context)  # type:ignore[no-any-return]


@pytest.fixture(name="connection_context")
def fx_connection_context() -> ConnectionContext:
    return ConnectionContext(
        handler_id="handler_id",
        request_encoding_type=RequestEncodingType.JSON,
        default_deserializer=default_deserializer,
        type_decoders=PydanticInitPlugin.decoders(),
    )


def test_backend_parse_raw_json(backend_context: BackendContext, connection_context: ConnectionContext) -> None:
    assert (
        to_builtins(
            DTOBackend(context=backend_context).parse_raw(
                b'{"a":1,"nested":{"a":1,"b":"two"},"nested_list":[{"a":1,"b":"two"}]}', connection_context
            )
        )
        == DESTRUCTURED
    )


def test_backend_parse_raw_msgpack(backend_context: BackendContext, connection_context: ConnectionContext) -> None:
    connection_context.request_encoding_type = MediaType.MESSAGEPACK  # type:ignore[misc]
    assert (
        to_builtins(
            DTOBackend(context=backend_context).parse_raw(
                b"\x83\xa1a\x01\xa6nested\x82\xa1a\x01\xa1b\xa3two\xabnested_list\x91\x82\xa1a\x01\xa1b\xa3two",
                connection_context,
            )
        )
        == DESTRUCTURED
    )


def test_backend_parse_unsupported_media_type(
    backend_context: BackendContext, connection_context: ConnectionContext
) -> None:
    connection_context.request_encoding_type = MediaType.CSS  # type:ignore[misc]
    with pytest.raises(SerializationException):
        DTOBackend(context=backend_context).parse_raw(b"", connection_context)


def test_backend_iterable_annotation(backend_context: BackendContext) -> None:
    backend_context.field_definition = FieldDefinition.from_annotation(List[DC])  # type:ignore[misc]
    backend = DTOBackend(backend_context)
    field_definition = FieldDefinition.from_annotation(backend.annotation)
    assert field_definition.origin is list
    assert field_definition.has_inner_subclass_of(Struct)


def test_backend_scalar_annotation(backend_context: BackendContext) -> None:
    backend = DTOBackend(backend_context)
    assert FieldDefinition.from_annotation(backend.annotation).is_subclass_of(Struct)


def test_backend_populate_data_from_builtins(
    backend_context: BackendContext, connection_context: ConnectionContext
) -> None:
    backend = DTOBackend(backend_context)
    data = backend.populate_data_from_builtins(builtins=DESTRUCTURED, connection_context=connection_context)
    assert data == STRUCTURED


def test_backend_create_openapi_schema(backend_context: BackendContext) -> None:
    backend = DTOBackend(backend_context)
    schemas: dict[str, Any] = {}
    ref = backend.create_openapi_schema(SchemaCreator(schemas=schemas))
    assert isinstance(ref, Reference)
    schema = schemas[ref.value]
    assert schema.properties["a"].type == "integer"
    assert schema.properties["b"].type == "string"
    assert schema.properties["c"].items.type == "integer"
    assert schema.properties["c"].type == "array"
    assert isinstance(nested := schema.properties["nested"], Reference)
    nested_schema = schemas[nested.value]
    assert nested_schema.properties["a"].type == "integer"
    assert nested_schema.properties["b"].type == "string"


def test_backend_model_name_uniqueness(backend_context: BackendContext) -> None:
    backend = DTOBackend(backend_context)
    unique_names: set = set()
    transfer_type = SimpleType(field_definition=FieldDefinition.from_annotation(int), nested_field_info=None)
    field_definition = FieldDefinition.from_kwarg(annotation=int, name="a")
    field_definition = DTOFieldDefinition.from_field_definition(
        field_definition=field_definition,
        default_factory=None,
        dto_field=DTOField(),
        unique_model_name="some_module.SomeModel",
        dto_for=None,
    )
    fd = (
        TransferDTOFieldDefinition.from_dto_field_definition(
            field_definition=field_definition,
            serialization_name="a",
            transfer_type=transfer_type,
            is_partial=False,
            is_excluded=False,
        ),
    )
    for _ in range(100):
        model_class = backend.create_transfer_model_type("some_module.SomeModel", fd)
        model_name = model_class.__name__
        assert model_name not in unique_names
        unique_names.add(model_name)


def test_backend_populate_data_from_raw(backend_context: BackendContext, connection_context: ConnectionContext) -> None:
    backend = DTOBackend(backend_context)
    data = backend.populate_data_from_raw(RAW, connection_context)
    assert data == STRUCTURED


def test_backend_populate_collection_data_from_raw(
    backend_context: BackendContext, connection_context: ConnectionContext
) -> None:
    backend_context.field_definition = FieldDefinition.from_annotation(List[DC])  # type:ignore[misc]
    backend = DTOBackend(backend_context)
    data = backend.populate_data_from_raw(COLLECTION_RAW, connection_context)
    assert data == [STRUCTURED]


def test_backend_encode_data(backend_context: BackendContext, connection_context: ConnectionContext) -> None:
    backend = DTOBackend(backend_context)
    data = backend.encode_data(STRUCTURED, connection_context)
    assert encode_json(data) == RAW


def test_backend_encode_collection_data(connection_context: ConnectionContext) -> None:
    ctx = BackendContext(
        dto_config=DTOConfig(),
        dto_for="data",
        field_definition=FieldDefinition.from_annotation(List[DC]),
        field_definition_generator=DataclassDTO.generate_field_definitions,
        is_nested_field_predicate=DataclassDTO.detect_nested_field,
        model_type=DC,
        wrapper_attribute_name=None,
    )
    backend = DTOBackend(ctx)
    data = backend.encode_data([STRUCTURED], connection_context)
    assert encode_json(data) == COLLECTION_RAW


def test_parse_model_nested_exclude(create_module: Callable[[str], ModuleType]) -> None:
    module = create_module(
        """
from dataclasses import dataclass
from typing import List

from litestar.dto import DataclassDTO

@dataclass
class NestedNestedModel:
    e: int
    f: int

@dataclass
class NestedModel:
    c: int
    d: List[NestedNestedModel]

@dataclass
class Model:
    a: int
    b: NestedModel

dto_type = DataclassDTO[Model]
    """
    )
    config = DTOConfig(max_nested_depth=2, exclude={"a", "b.c", "b.d.0.e"})
    ctx = BackendContext(
        dto_config=config,
        dto_for="data",
        field_definition=FieldDefinition.from_annotation(module.Model),
        field_definition_generator=DataclassDTO.generate_field_definitions,
        is_nested_field_predicate=DataclassDTO.detect_nested_field,
        model_type=module.Model,
        wrapper_attribute_name=None,
    )
    parsed = DTOBackend(context=ctx).parsed_field_definitions
    assert next(f for f in parsed if f.name == "a").is_excluded
    assert parsed[1].name == "b"
    b_transfer_type = parsed[1].transfer_type
    assert isinstance(b_transfer_type, SimpleType)
    b_nested_info = b_transfer_type.nested_field_info
    assert b_nested_info is not None
    assert next(f for f in b_nested_info.field_definitions if f.name == "c").is_excluded
    assert b_nested_info.field_definitions[1].name == "d"
    b_d_transfer_type = b_nested_info.field_definitions[1].transfer_type
    assert isinstance(b_d_transfer_type, CollectionType)
    assert isinstance(b_d_transfer_type.inner_type, SimpleType)
    b_d_nested_info = b_d_transfer_type.inner_type.nested_field_info
    assert b_d_nested_info is not None
    assert next(f for f in b_d_nested_info.field_definitions if f.name == "e").is_excluded
    assert b_d_nested_info.field_definitions[1].name == "f"


def test_parse_model_nested_include(create_module: Callable[[str], ModuleType]) -> None:
    module = create_module(
        """
from dataclasses import dataclass
from typing import List

from litestar.dto import DataclassDTO

@dataclass
class NestedNestedModel:
    e: int
    f: int

@dataclass
class NestedModel:
    c: int
    d: List[NestedNestedModel]

@dataclass
class Model:
    a: int
    b: NestedModel

dto_type = DataclassDTO[Model]
    """
    )
    config = DTOConfig(max_nested_depth=2, include={"a", "b.c", "b.d.0.e"})
    ctx = BackendContext(
        dto_config=config,
        dto_for="data",
        field_definition=FieldDefinition.from_annotation(module.Model),
        field_definition_generator=DataclassDTO.generate_field_definitions,
        is_nested_field_predicate=DataclassDTO.detect_nested_field,
        model_type=module.Model,
        wrapper_attribute_name=None,
    )
    parsed = DTOBackend(context=ctx).parsed_field_definitions
    assert not next(f for f in parsed if f.name == "a").is_excluded
    assert parsed[1].name == "b"
    b_transfer_type = parsed[1].transfer_type
    assert isinstance(b_transfer_type, SimpleType)
    b_nested_info = b_transfer_type.nested_field_info
    assert b_nested_info is not None
    assert not next(f for f in b_nested_info.field_definitions if f.name == "c").is_excluded
    assert b_nested_info.field_definitions[1].name == "d"
    b_d_transfer_type = b_nested_info.field_definitions[1].transfer_type
    assert isinstance(b_d_transfer_type, CollectionType)
    assert isinstance(b_d_transfer_type.inner_type, SimpleType)
    b_d_nested_info = b_d_transfer_type.inner_type.nested_field_info
    assert b_d_nested_info is not None
    assert not next(f for f in b_d_nested_info.field_definitions if f.name == "e").is_excluded
    assert b_d_nested_info.field_definitions[1].name == "f"
