from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

import pytest

from litestar.dto.factory import DTOConfig
from litestar.dto.factory.types import FieldDefinition
from litestar.dto.factory._backends.abc import AbstractDTOBackend, BackendContext
from litestar.dto.factory._backends.types import UnionType, SimpleType
from litestar.types.empty import Empty
from litestar.utils.signature import ParsedType

if TYPE_CHECKING:
    from typing import AbstractSet

    from litestar.dto.factory._backends.types import FieldDefinitionsType, TransferType
    from litestar.dto.interface import ConnectionContext


@dataclass
class Model:
    a: int
    b: str


@dataclass
class Model2:
    c: int
    d: str


@pytest.fixture(name="data_model_type")
def fx_data_model_type() -> type[Model]:
    return type("Model", (Model,), {})


@pytest.fixture(name="data_model")
def fx_data_model(data_model_type: type[Model]) -> Model:
    return data_model_type(a=1, b="2")


@pytest.fixture(name="context")
def fx_context(data_model_type: type[Model]) -> BackendContext:
    return BackendContext(
        dto_config=DTOConfig(),
        dto_for="data",
        parsed_type=ParsedType(data_model_type),
        field_definition_generator=lambda anything: (
            f
            for f in [
                FieldDefinition(
                    name="a",
                    default=Empty,
                    parsed_type=ParsedType(int),
                    default_factory=None,
                    dto_field=None,
                    unique_model_name="some_module.SomeModel",
                ),
                FieldDefinition(
                    name="b",
                    default=Empty,
                    parsed_type=ParsedType(str),
                    default_factory=None,
                    dto_field=None,
                    unique_model_name="some_module.SomeModel",
                ),
            ]
        ),
        is_nested_field_predicate=lambda parsed_type: parsed_type.is_subclass_of((Model, Model2)),
        model_type=data_model_type,
    )


@pytest.fixture(name="backend")
def fx_backend(context: BackendContext) -> AbstractDTOBackend:
    class _Backend(AbstractDTOBackend[Any]):
        def create_transfer_model_type(self, unique_name: str, field_definitions: FieldDefinitionsType) -> type[Any]:
            """Create a model for data transfer.

            Args:
            unique_name: name for the type that should be unique across all transfer types.
            field_definitions: field definitions for the container type.

            Returns:
            A ``BackendT`` class.
            """
            return Model

        def parse_raw(self, raw: bytes, connection_context: ConnectionContext) -> Any:
            """Parse raw bytes into transfer model type.

            Args:
            raw: bytes
            connection_context: Information about the active connection.

            Returns:
            The raw bytes parsed into transfer model type.
            """
            return None

        def parse_builtins(self, builtins: Any, connection_context: ConnectionContext) -> Any:
            """Parse builtin types into transfer model type.

            Args:
            builtins: Builtin type.
            connection_context: Information about the active connection.

            Returns:
            The builtin type parsed into transfer model type.
            """
            return None

    return _Backend(context)


def create_transfer_type(
    backend: AbstractDTOBackend,
    parsed_type: ParsedType,
    exclude: AbstractSet[str] | None = None,
    field_name: str = "name",
    unique_name: str = "some_module.SomeModel.name",
    nested_depth: int = 0,
) -> TransferType:
    return backend._create_transfer_type(parsed_type, exclude or set(), field_name, unique_name, nested_depth)


@pytest.mark.parametrize(
    (
        "parsed_type",
        "should_have_nested",
        "has_nested_field_info",
    ),
    [
        (ParsedType(Union[Model, None]), True, (True, False)),
        (ParsedType(Union[Model, str]), True, (True, False)),
        (ParsedType(Union[Model, int]), True, (True, False)),
        (ParsedType(Union[Model, Model2]), True, (True, True)),
        (ParsedType(Union[int, str]), False, (False, False)),
    ],
)
def test_create_transfer_type_union(
    parsed_type: ParsedType,
    should_have_nested: bool,
    has_nested_field_info: tuple[bool, ...],
    backend: AbstractDTOBackend,
) -> None:
    transfer_type = create_transfer_type(backend, parsed_type)
    assert isinstance(transfer_type, UnionType)
    assert transfer_type.has_nested is should_have_nested
    inner_types = transfer_type.inner_types
    assert len(inner_types) == len(transfer_type.parsed_type.inner_types)
    for inner_type, has_nested in zip(inner_types, has_nested_field_info):
        assert isinstance(inner_type, SimpleType)
        assert bool(inner_type.nested_field_info) is has_nested
