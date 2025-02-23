from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Iterable, Iterator, Sequence
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from litestar.response.sse import ServerSentEventMessage


T = TypeVar("T")

__all__ = ("AnyIOBackend", "MaybePartial", "OptionalSequence", "SSEData", "StreamType", "SyncOrAsyncUnion")

OptionalSequence: TypeAlias = Optional[Sequence[T]]
"""Types 'T' as union of Sequence[T] and None."""

SyncOrAsyncUnion: TypeAlias = Union[T, Awaitable[T]]
"""Types 'T' as a union of T and awaitable T."""


AnyIOBackend: TypeAlias = Literal["asyncio", "trio"]
"""Anyio backend names."""

StreamType: TypeAlias = Union[Iterable[T], Iterator[T], AsyncIterable[T], AsyncIterator[T]]
"""A stream type."""

MaybePartial: TypeAlias = Union[T, partial]
"""A potentially partial callable."""

SSEData: TypeAlias = Union[int, str, bytes, dict[str, Any], "ServerSentEventMessage"]
"""A type alias for SSE data."""
