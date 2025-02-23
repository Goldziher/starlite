from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

import pytest

from litestar.connection import ASGIConnection
from litestar.dto import DataclassDTO, DTOConfig, DTOField
from litestar.dto._backend import DTOBackend
from litestar.dto._types import (
    CollectionType,
    CompositeType,
    MappingType,
    SimpleType,
    TransferDTOFieldDefinition,
    TupleType,
    UnionType,
)
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.types import DataclassProtocol
from litestar.typing import FieldDefinition

if TYPE_CHECKING:
    from collections.abc import Set

    from litestar.dto._types import TransferType


@dataclass
class Model:
    a: int
    b: str


@dataclass
class Model2:
    c: int
    d: str


@pytest.fixture(name="data_model_type")
def fx_data_model_type() -> Any:
    return type("Model", (Model,), {})


@pytest.fixture(name="data_model")
def fx_data_model(data_model_type: type[Model]) -> Model:
    return data_model_type(a=1, b="2")


@pytest.fixture(name="field_definitions")
def fx_field_definitions(data_model_type: type[Model]) -> list[DTOFieldDefinition]:
    return [
        DTOFieldDefinition.from_field_definition(
            field_definition=FieldDefinition.from_kwarg(
                annotation=int,
                name="a",
            ),
            default_factory=None,
            dto_field=DTOField(),
            model_name="some_module.SomeModel",
        ),
        DTOFieldDefinition.from_field_definition(
            field_definition=FieldDefinition.from_kwarg(
                annotation=str,
                name="b",
            ),
            default_factory=None,
            dto_field=DTOField(),
            model_name="some_module.SomeModel",
        ),
    ]


@pytest.fixture(name="backend")
def fx_backend(
    data_model_type: type[Model],
    field_definitions: list[DTOFieldDefinition],
    backend_cls: type[DTOBackend],
    use_experimental_dto_backend: bool,
) -> DTOBackend:
    class _Factory(DataclassDTO):
        config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

        @classmethod
        def generate_field_definitions(
            cls, model_type: type[DataclassProtocol]
        ) -> Generator[DTOFieldDefinition, None, None]:
            yield from field_definitions

    class _Backend(backend_cls):  # type: ignore[valid-type,misc]
        def create_transfer_model_type(
            self, model_name: str, field_definitions: tuple[TransferDTOFieldDefinition, ...]
        ) -> type[Any]:
            """Create a model for data transfer.

            Args:
            unique_name: name for the type that should be unique across all transfer types.
            field_definitions: field definitions for the container type.

            Returns:
            A ``BackendT`` class.
            """
            return Model

        def parse_raw(self, raw: bytes, asgi_connection: ASGIConnection) -> Any:
            """Parse raw bytes into transfer model type.

            Args:
            raw: bytes
            asgi_connection: Information about the active connection.

            Returns:
            The raw bytes parsed into transfer model type.
            """
            return None

        def parse_builtins(self, builtins: Any, asgi_connection: ASGIConnection) -> Any:
            """Parse builtin types into transfer model type.

            Args:
            builtins: Builtin type.
            asgi_connection: Information about the active connection.

            Returns:
            The builtin type parsed into transfer model type.
            """
            return None

    return _Backend(
        dto_factory=_Factory,
        is_data_field=True,
        field_definition=FieldDefinition.from_annotation(data_model_type),
        model_type=data_model_type,
        wrapper_attribute_name=None,
        handler_id="test",
    )


def create_transfer_type(
    backend: DTOBackend,
    field_definition: FieldDefinition,
    exclude: Set[str] | None = None,
    include: Set[str] | None = None,
    field_name: str = "name",
    unique_name: str = "some_module.SomeModel.name",
    nested_depth: int = 0,
    rename_fields: dict[str, str] | None = None,
) -> TransferType:
    return backend._create_transfer_type(
        field_definition=field_definition,
        exclude=exclude or set(),
        include=include or set(),
        field_name=field_name,
        unique_name=unique_name,
        nested_depth=nested_depth,
        rename_fields=rename_fields or {},
    )


@pytest.mark.parametrize(
    ("field_definition", "should_have_nested", "has_nested_field_info"),
    [
        (FieldDefinition.from_annotation(Union[Model, None]), True, (True, False)),
        (FieldDefinition.from_annotation(Union[Model, str]), True, (True, False)),
        (FieldDefinition.from_annotation(Union[Model, int]), True, (True, False)),
        (FieldDefinition.from_annotation(Union[Model, Model2]), True, (True, True)),
        (FieldDefinition.from_annotation(Union[int, str]), False, (False, False)),
    ],
)
def test_create_transfer_type_union(
    field_definition: FieldDefinition,
    should_have_nested: bool,
    has_nested_field_info: tuple[bool, ...],
    backend: DTOBackend,
) -> None:
    transfer_type = create_transfer_type(backend, field_definition)
    assert isinstance(transfer_type, UnionType)
    assert transfer_type.has_nested is should_have_nested
    inner_types = transfer_type.inner_types
    assert len(inner_types) == len(transfer_type.field_definition.inner_types)
    for inner_type, has_nested in zip(inner_types, has_nested_field_info):
        assert isinstance(inner_type, SimpleType)
        assert bool(inner_type.nested_field_info) is has_nested


@pytest.mark.parametrize(
    ("field_definition", "should_have_nested", "has_nested_field_info"),
    [
        (FieldDefinition.from_annotation(tuple[Model, None]), True, (True, False)),
        (FieldDefinition.from_annotation(tuple[Model, str]), True, (True, False)),
        (FieldDefinition.from_annotation(tuple[Model, int]), True, (True, False)),
        (FieldDefinition.from_annotation(tuple[Model, Model2]), True, (True, True)),
        (FieldDefinition.from_annotation(tuple[int, str]), False, (False, False)),
        (FieldDefinition.from_annotation(tuple[Model, ...]), True, (True,)),
        (FieldDefinition.from_annotation(tuple[int, ...]), False, (False,)),
    ],
)
def test_create_transfer_type_tuple(
    field_definition: FieldDefinition,
    should_have_nested: bool,
    has_nested_field_info: tuple[bool, ...],
    backend: DTOBackend,
) -> None:
    transfer_type = create_transfer_type(backend, field_definition)
    assert isinstance(transfer_type, CompositeType)
    assert transfer_type.has_nested is should_have_nested
    if field_definition.inner_types[-1].annotation is Ellipsis:
        assert isinstance(transfer_type, CollectionType)
        inner_type = transfer_type.inner_type
        assert isinstance(inner_type, SimpleType)
        assert bool(inner_type.nested_field_info) is has_nested_field_info[0]
    else:
        assert isinstance(transfer_type, TupleType)
        inner_types = transfer_type.inner_types
        assert len(inner_types) == len(transfer_type.field_definition.inner_types)
        for inner_type, has_nested in zip(inner_types, has_nested_field_info):
            assert isinstance(inner_type, SimpleType)
            assert bool(inner_type.nested_field_info) is has_nested


@pytest.mark.parametrize(
    ("field_definition", "should_have_nested", "has_nested_field_info"),
    [
        (FieldDefinition.from_annotation(dict[Model, None]), True, (True, False)),
        (FieldDefinition.from_annotation(dict[Model, str]), True, (True, False)),
        (FieldDefinition.from_annotation(dict[Model, int]), True, (True, False)),
        (FieldDefinition.from_annotation(dict[Model, Model2]), True, (True, True)),
        (FieldDefinition.from_annotation(dict[int, str]), False, (False, False)),
    ],
)
def test_create_transfer_type_mapping(
    field_definition: FieldDefinition,
    should_have_nested: bool,
    has_nested_field_info: tuple[bool, ...],
    backend: DTOBackend,
) -> None:
    transfer_type = create_transfer_type(backend, field_definition)
    assert isinstance(transfer_type, MappingType)
    assert transfer_type.has_nested is should_have_nested
    key_type = transfer_type.key_type
    value_type = transfer_type.value_type
    for inner_type, has_nested in zip((key_type, value_type), has_nested_field_info):
        assert isinstance(inner_type, SimpleType)
        assert bool(inner_type.nested_field_info) is has_nested


@pytest.mark.parametrize(
    ("field_definition", "should_have_nested", "has_nested_field_info"),
    [
        (FieldDefinition.from_annotation(list[Model]), True, True),
        (FieldDefinition.from_annotation(list[int]), False, False),
    ],
)
def test_create_transfer_type_collection(
    field_definition: FieldDefinition,
    should_have_nested: bool,
    has_nested_field_info: bool,
    backend: DTOBackend,
) -> None:
    transfer_type = create_transfer_type(backend, field_definition)
    assert isinstance(transfer_type, CollectionType)
    assert transfer_type.has_nested is should_have_nested
    inner_type = transfer_type.inner_type
    assert isinstance(inner_type, SimpleType)
    assert bool(inner_type.nested_field_info) is has_nested_field_info


def test_create_collection_type_nested_union(backend: DTOBackend) -> None:
    field_definition = FieldDefinition.from_annotation(list[Union[Model, Model2]])
    transfer_type = create_transfer_type(backend, field_definition)
    assert isinstance(transfer_type, CollectionType)
    assert transfer_type.has_nested is True
    inner_type = transfer_type.inner_type
    assert isinstance(inner_type, UnionType)
    assert inner_type.has_nested is True
    inner_types = inner_type.inner_types
    assert len(inner_types) == len(inner_type.field_definition.inner_types)
    for inner_type in inner_types:
        assert isinstance(inner_type, SimpleType)
        assert bool(inner_type.nested_field_info)
