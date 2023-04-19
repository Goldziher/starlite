from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from litestar.dto.interface import DTOInterface
from litestar.types.protocols import DataclassProtocol
from litestar.types.serialization import LitestarEncodableType

if TYPE_CHECKING:
    from typing import Any

    from litestar.connection import Request


@dataclass
class Model:
    a: int
    b: str


class MockDTO(DTOInterface):
    def __init__(self, connection: Request[Any, Any, Any]) -> None:
        pass

    def builtins_to_data_type(self, builtins: Any) -> Model:
        return Model(a=1, b="2")

    def bytes_to_data_type(self, raw: bytes) -> Model:
        return Model(a=1, b="2")

    def data_to_encodable_type(self, data: DataclassProtocol) -> bytes | LitestarEncodableType:
        return Model(a=1, b="2")


class MockReturnDTO(DTOInterface):
    def __init__(self, connection: Request[Any, Any, Any]) -> None:
        pass

    def builtins_to_data_type(self, builtins: Any) -> Model:
        raise RuntimeError("Return DTO should not have this method called")

    def bytes_to_data_type(self, raw: bytes) -> Any:
        raise RuntimeError("Return DTO should not have this method called")

    def data_to_encodable_type(self, data: DataclassProtocol) -> bytes | LitestarEncodableType:
        return b'{"a": 1, "b": "2"}'
