from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections import deque
    from collections.abc import Collection
    from datetime import date, datetime, time
    from decimal import Decimal
    from enum import Enum, IntEnum
    from ipaddress import (
        IPv4Address,
        IPv4Interface,
        IPv4Network,
        IPv6Address,
        IPv6Interface,
        IPv6Network,
    )
    from pathlib import Path, PurePath
    from re import Pattern
    from uuid import UUID

    from msgspec import Raw, Struct
    from msgspec.msgpack import Ext
    from typing_extensions import TypeAlias

    from litestar.types import DataclassProtocol, TypedDictClass

    try:
        from pydantic import BaseModel
        from pydantic.main import IncEx
        from pydantic.typing import AbstractSetIntStr, MappingIntStrAny
    except ImportError:
        BaseModel = Any  # type: ignore[assignment, misc]
        IncEx = Any  # type: ignore[misc]
        AbstractSetIntStr = Any
        MappingIntStrAny = Any

    try:
        from attrs import AttrsInstance
    except ImportError:
        AttrsInstance = Any  # type: ignore[assignment, misc]

__all__ = (
    "DataContainerType",
    "EncodableBuiltinCollectionType",
    "EncodableBuiltinType",
    "EncodableMsgSpecType",
    "EncodableStdLibIPType",
    "EncodableStdLibType",
    "LitestarEncodableType",
)

EncodableBuiltinType: TypeAlias = "None | bool | int | float | str | bytes | bytearray"
EncodableBuiltinCollectionType: TypeAlias = "list | tuple | set | frozenset | dict | Collection"
EncodableStdLibType: TypeAlias = (
    "date | datetime | deque | time | UUID | Decimal | Enum | IntEnum | DataclassProtocol | Path | PurePath | Pattern"
)
EncodableStdLibIPType: TypeAlias = (
    "IPv4Address | IPv4Interface | IPv4Network | IPv6Address | IPv6Interface | IPv6Network"
)
EncodableMsgSpecType: TypeAlias = "Ext | Raw | Struct"
LitestarEncodableType: TypeAlias = "EncodableBuiltinType | EncodableBuiltinCollectionType | EncodableStdLibType | EncodableStdLibIPType | EncodableMsgSpecType | BaseModel | AttrsInstance"  # pyright: ignore
DataContainerType: TypeAlias = "Struct | BaseModel | AttrsInstance | TypedDictClass | DataclassProtocol"  # pyright: ignore
PydanticV2FieldsListType: TypeAlias = "set[int] | set[str] | dict[int, Any] | dict[str, Any]"
PydanticV1FieldsListType: TypeAlias = "IncEx | AbstractSetIntStr | MappingIntStrAny"  # pyright: ignore
