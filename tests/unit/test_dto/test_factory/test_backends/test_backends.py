# ruff: noqa: UP006,UP007
from __future__ import annotations

from dataclasses import dataclass, field
from types import ModuleType
from typing import TYPE_CHECKING, Callable, List, Optional
from unittest.mock import MagicMock

import pytest
from msgspec import Struct, to_builtins

from litestar import Litestar, Request, get, post
from litestar._openapi.schema_generation import SchemaCreator
from litestar.dto import DataclassDTO, DTOConfig, DTOField
from litestar.dto._backend import DTOBackend
from litestar.dto._types import CollectionType, SimpleType, TransferDTOFieldDefinition
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.enums import MediaType
from litestar.exceptions import SerializationException
from litestar.openapi.spec.reference import Reference
from litestar.openapi.spec.schema import Schema
from litestar.serialization import encode_json
from litestar.testing import RequestFactory
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


@pytest.fixture(name="dto_factory")
def fx_backend_factory(use_experimental_dto_backend: bool) -> type[DataclassDTO]:
    class Factory(DataclassDTO):
        config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)
        model_type = DC

    return Factory


@pytest.fixture(name="asgi_connection")
def fx_asgi_connection() -> Request[Any, Any, Any]:
    @get("/", name="handler_id", media_type=MediaType.JSON)
    def _handler() -> None:
        ...

    return RequestFactory().get(path="/", route_handler=_handler)


def test_backend_parse_raw_json(
    dto_factory: type[DataclassDTO], asgi_connection: Request[Any, Any, Any], backend_cls: type[DTOBackend]
) -> None:
    assert (
        to_builtins(
            backend_cls(
                dto_factory=dto_factory,
                field_definition=FieldDefinition.from_annotation(DC),
                model_type=DC,
                wrapper_attribute_name=None,
                is_data_field=True,
                handler_id="test",
            ).parse_raw(b'{"a":1,"nested":{"a":1,"b":"two"},"nested_list":[{"a":1,"b":"two"}]}', asgi_connection)
        )
        == DESTRUCTURED
    )


def test_backend_parse_raw_msgpack(dto_factory: type[DataclassDTO], backend_cls: type[DTOBackend]) -> None:
    @get("/", name="handler_id", media_type=MediaType.MESSAGEPACK)
    def _handler() -> None:
        ...

    asgi_connection = RequestFactory().get(
        path="/", route_handler=_handler, headers={"Content-Type": MediaType.MESSAGEPACK}
    )
    assert (
        to_builtins(
            backend_cls(
                dto_factory=dto_factory,
                field_definition=FieldDefinition.from_annotation(DC),
                model_type=DC,
                wrapper_attribute_name=None,
                is_data_field=True,
                handler_id="test",
            ).parse_raw(
                b"\x83\xa1a\x01\xa6nested\x82\xa1a\x01\xa1b\xa3two\xabnested_list\x91\x82\xa1a\x01\xa1b\xa3two",
                asgi_connection,
            )
        )
        == DESTRUCTURED
    )


def test_backend_parse_unsupported_media_type(
    dto_factory: type[DataclassDTO], asgi_connection: Request[Any, Any, Any], backend_cls: type[DTOBackend]
) -> None:
    @get("/", name="handler_id", media_type="text/css")
    def _handler() -> None:
        ...

    asgi_connection = RequestFactory().get(path="/", route_handler=_handler, headers={"Content-Type": "text/css"})

    with pytest.raises(SerializationException):
        backend_cls(
            dto_factory=dto_factory,
            field_definition=FieldDefinition.from_annotation(DC),
            model_type=DC,
            wrapper_attribute_name=None,
            is_data_field=True,
            handler_id="test",
        ).parse_raw(b"", asgi_connection)


def test_backend_iterable_annotation(dto_factory: type[DataclassDTO], backend_cls: type[DTOBackend]) -> None:
    backend = DTOBackend(
        handler_id="test",
        dto_factory=dto_factory,
        field_definition=FieldDefinition.from_annotation(List[DC]),
        model_type=DC,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    field_definition = FieldDefinition.from_annotation(backend.annotation)
    assert field_definition.origin is list
    assert field_definition.has_inner_subclass_of(Struct)


def test_backend_scalar_annotation(dto_factory: type[DataclassDTO], backend_cls: type[DTOBackend]) -> None:
    backend = backend_cls(
        handler_id="test",
        dto_factory=dto_factory,
        field_definition=FieldDefinition.from_annotation(DC),
        model_type=DC,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    assert FieldDefinition.from_annotation(backend.annotation).is_subclass_of(Struct)


def test_backend_populate_data_from_builtins(
    dto_factory: type[DataclassDTO], asgi_connection: Request[Any, Any, Any], backend_cls: type[DTOBackend]
) -> None:
    backend = backend_cls(
        handler_id="test",
        dto_factory=dto_factory,
        field_definition=FieldDefinition.from_annotation(DC),
        model_type=DC,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    data = backend.populate_data_from_builtins(builtins=DESTRUCTURED, asgi_connection=asgi_connection)
    assert data == STRUCTURED


def test_backend_create_openapi_schema(dto_factory: type[DataclassDTO]) -> None:
    @post("/", dto=dto_factory, name="test")
    def handler(data: DC) -> DC:
        return data

    app = Litestar(route_handlers=[handler])

    creator = SchemaCreator(plugins=app.plugins.openapi)
    ref = dto_factory.create_openapi_schema(
        handler_id=app.get_handler_index_by_name("test")["handler"].handler_id,  # type: ignore[index]
        field_definition=FieldDefinition.from_annotation(DC),
        schema_creator=creator,
    )
    schemas = creator.schema_registry.generate_components_schemas()
    assert isinstance(ref, Reference)
    schema = schemas[ref.value]
    assert schema.properties is not None
    a, b, c = schema.properties["a"], schema.properties["b"], schema.properties["c"]
    assert isinstance(a, Schema)
    assert a.type == "integer"
    assert isinstance(b, Schema)
    assert b.type == "string"
    assert isinstance(c, Schema)
    assert c.type == "array"
    assert isinstance(c.items, Schema)
    assert c.items.type == "integer"
    assert isinstance(nested := schema.properties["nested"], Reference)  # noqa: RUF018
    nested_schema = schemas[nested.value]
    assert nested_schema.properties is not None
    nested_a, nested_b = nested_schema.properties["a"], nested_schema.properties["b"]
    assert isinstance(nested_a, Schema)
    assert nested_a.type == "integer"
    assert isinstance(nested_b, Schema)
    assert nested_b.type == "string"


def test_backend_model_name_uniqueness(dto_factory: type[DataclassDTO], backend_cls: type[DTOBackend]) -> None:
    backend = backend_cls(
        handler_id="test",
        dto_factory=dto_factory,
        field_definition=FieldDefinition.from_annotation(DC),
        model_type=DC,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    backend._seen_model_names.clear()
    unique_names: set = set()

    field_definition = TransferDTOFieldDefinition.from_dto_field_definition(
        field_definition=DTOFieldDefinition.from_field_definition(
            field_definition=FieldDefinition.from_kwarg(annotation=int, name="a"),
            default_factory=None,
            dto_field=DTOField(),
            model_name="some_module.SomeModel",
        ),
        serialization_name="a",
        transfer_type=SimpleType(field_definition=FieldDefinition.from_annotation(int), nested_field_info=None),
        is_partial=False,
        is_excluded=False,
    )

    for _ in range(100):
        model_class = backend.create_transfer_model_type("some_module.SomeModel", field_definitions=(field_definition,))
        unique_names.add(model_class.__name__)

    assert len(unique_names) == 100
    assert backend._seen_model_names == unique_names


def test_backend_populate_data_from_raw(
    dto_factory: type[DataclassDTO], asgi_connection: Request[Any, Any, Any], backend_cls: type[DTOBackend]
) -> None:
    backend = backend_cls(
        handler_id="test",
        dto_factory=dto_factory,
        field_definition=FieldDefinition.from_annotation(DC),
        model_type=DC,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    data = backend.populate_data_from_raw(RAW, asgi_connection)
    assert data == STRUCTURED


def test_backend_populate_collection_data_from_raw(
    dto_factory: type[DataclassDTO], asgi_connection: Request[Any, Any, Any], backend_cls: type[DTOBackend]
) -> None:
    backend = backend_cls(
        handler_id="test",
        dto_factory=dto_factory,
        field_definition=FieldDefinition.from_annotation(List[DC]),
        model_type=DC,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    data = backend.populate_data_from_raw(COLLECTION_RAW, asgi_connection)
    assert data == [STRUCTURED]


def test_backend_encode_data(
    dto_factory: type[DataclassDTO], asgi_connection: Request[Any, Any, Any], backend_cls: type[DTOBackend]
) -> None:
    backend = backend_cls(
        handler_id="test",
        dto_factory=dto_factory,
        field_definition=FieldDefinition.from_annotation(DC),
        model_type=DC,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    data = backend.encode_data(STRUCTURED)
    assert encode_json(data) == RAW


def test_backend_encode_collection_data(
    dto_factory: type[DataclassDTO], asgi_connection: Request[Any, Any, Any], backend_cls: type[DTOBackend]
) -> None:
    backend = backend_cls(
        handler_id="test",
        dto_factory=dto_factory,
        field_definition=FieldDefinition.from_annotation(List[DC]),
        model_type=DC,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    data = backend.encode_data([STRUCTURED])
    assert encode_json(data) == COLLECTION_RAW


def test_transfer_only_touches_included_attributes(backend_cls: type[DTOBackend]) -> None:
    """Ensure attribute that are not included are never touched in any way during
    transfer.

    https://github.com/litestar-org/litestar/issues/2125
    """
    mock = MagicMock()

    @dataclass()
    class Foo:
        id: str
        bar: str = ""

    class Factory(DataclassDTO):
        config = DTOConfig(include={"excluded"})

    backend = backend_cls(
        handler_id="test",
        dto_factory=Factory,
        field_definition=TransferDTOFieldDefinition.from_annotation(Foo),
        model_type=Foo,
        wrapper_attribute_name=None,
        is_data_field=False,
    )

    Foo.bar = property(fget=lambda s: mock(return_value=""), fset=lambda s, v: None)  # type: ignore[assignment]

    backend.encode_data(Foo(id="1"))
    assert mock.call_count == 0


def test_parse_model_nested_exclude(create_module: Callable[[str], ModuleType], backend_cls: type[DTOBackend]) -> None:
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

    class Factory(DataclassDTO):
        config = DTOConfig(max_nested_depth=2, exclude={"a", "b.c", "b.d.0.e"})

    backend = backend_cls(
        handler_id="test",
        dto_factory=Factory,
        field_definition=FieldDefinition.from_annotation(module.Model),
        model_type=module.Model,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    parsed = backend.parsed_field_definitions
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


def test_parse_model_nested_include(create_module: Callable[[str], ModuleType], backend_cls: type[DTOBackend]) -> None:
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

    class Factory(DataclassDTO):
        config = DTOConfig(max_nested_depth=2, include={"a", "b.c", "b.d.0.e"})

    backend = backend_cls(
        handler_id="test",
        dto_factory=Factory,
        field_definition=FieldDefinition.from_annotation(module.Model),
        model_type=module.Model,
        wrapper_attribute_name=None,
        is_data_field=True,
    )
    parsed = backend.parsed_field_definitions
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
