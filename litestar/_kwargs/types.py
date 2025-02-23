from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, Callable

from typing_extensions import TypeAlias

from litestar.connection import ASGIConnection

Extractor: TypeAlias = Callable[[dict[str, Any], ASGIConnection], Awaitable[None]]
