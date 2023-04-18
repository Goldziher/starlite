from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from litestar.handlers import BaseRouteHandler
    from litestar.types import LitestarEncodableType
    from litestar.types.internal_types import AnyConnection
    from litestar.utils.signature import ParsedType

    from .types import ForType

__all__ = ("DTOInterface",)


@runtime_checkable
class DTOInterface(Protocol):
    __slots__ = ()

    @abstractmethod
    def __init__(self, connection: AnyConnection) -> None:
        """Initialize the DTO.

        Args:
            connection: :class:`ASGIConnection <.connection.ASGIConnection>` instance.
        """

    @abstractmethod
    def data_to_encodable_type(self, data: Any) -> bytes | LitestarEncodableType:
        """Encode data to a type supported by litestar serialization.

        Can return either bytes or a type that Litestar can return to bytes.

        Returns:
            Either ``bytes`` or a type that Litestar can convert to bytes.
        """

    @abstractmethod
    def bytes_to_data_type(self, raw: bytes) -> Any:
        """Convert raw bytes to the data type that the DTO represents.

        Args:
            raw: Raw bytes of the payload.

        Returns:
            Data type that the DTO represents.
        """

    @classmethod
    def on_registration(cls, route_handler: BaseRouteHandler, dto_for: ForType, parsed_type: ParsedType) -> None:
        """Receive the ``parsed_type`` and ``route_handler`` that this DTO is configured to represent.

        At this point, if the DTO type does not support the annotated type of ``parsed_type``, it should raise an
        ``UnsupportedType`` exception.

        Args:
            route_handler: :class:`HTTPRouteHandler <.handlers.HTTPRouteHandler>` DTO type is declared upon.
            parsed_type: :class:``ParsedType`` for represented  annotation.
            dto_for: indicates whether the DTO is for the request body or response.

        Raises:
            UnsupportedType: If the DTO type does not support the annotated type of ``parsed_type``.
        """
        return
