from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from collections import deque
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
    from pydantic import (
        BaseModel,
        ByteSize,
        ConstrainedBytes,
        ConstrainedDate,
        NameEmail,
        SecretField,
        StrictBool,
    )
    from pydantic.color import Color

    from starlite.types import DataclassProtocol

EncodableBuiltinType: TypeAlias = "None | bool | int | float | str | bytes | bytearray"
EncodableBuiltinCollectionType: TypeAlias = "list | tuple | set | frozenset | dict"
EncodableStdLibType: TypeAlias = (
    "date | datetime | deque | time | UUID | Decimal | Enum | IntEnum | DataclassProtocol | Path | PurePath | Pattern"
)
EncodableStdLibIPType: TypeAlias = (
    "IPv4Address | IPv4Interface | IPv4Network | IPv6Address | IPv6Interface | IPv6Network"
)
EncodableMsgSpecType: TypeAlias = "Ext | Raw | Struct"
EncodablePydanticType: TypeAlias = (
    "BaseModel | ByteSize | ConstrainedBytes | ConstrainedDate | NameEmail | SecretField | StrictBool | Color"
)

StarliteEncodableType: TypeAlias = "EncodableBuiltinType | EncodableBuiltinCollectionType | EncodableStdLibType | EncodableStdLibIPType | EncodableMsgSpecType | EncodablePydanticType"
