from __future__ import annotations

import sys
from typing import TYPE_CHECKING, TypeVar

from litestar.types import Empty, EmptyType

__all__ = ("async_next",)


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from typing import Any

T = TypeVar("T")
D = TypeVar("D")

if sys.version_info >= (3, 10):
    async_next = anext  # type: ignore[name-defined]  # noqa: F821
else:

    async def async_next(gen: AsyncGenerator[T, Any], default: D | EmptyType = Empty) -> T | D:
        """Backwards compatibility shim for Python<3.10."""
        try:
            return await gen.__anext__()
        except StopAsyncIteration as exc:
            if default is not Empty:
                return default
            raise exc
