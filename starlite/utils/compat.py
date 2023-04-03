from __future__ import annotations

import sys
from typing import TYPE_CHECKING, TypeVar

from starlite.types import Empty, EmptyType

__all__ = (
    "PY_VER",
    "async_next",
)


if TYPE_CHECKING:
    from typing import Any, AsyncGenerator

PY_VER = sys.version_info[:2]
T = TypeVar("T")
D = TypeVar("D")

try:
    async_next = anext  # pyright: ignore
except NameError:  # pragma: no cover

    async def async_next(gen: AsyncGenerator[T, Any], default: D | EmptyType = Empty) -> T | D:  # type: ignore[misc]
        """Backwards compatibility shim for Python<3.10."""
        try:
            return await gen.__anext__()
        except StopAsyncIteration as exc:
            if default is not Empty:
                return default  # type: ignore[return-value]
            raise exc
