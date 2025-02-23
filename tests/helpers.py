from __future__ import annotations

import atexit
import importlib.util
import inspect
import logging
import random
import sys
from collections.abc import Awaitable, Generator
from contextlib import AbstractAsyncContextManager, AbstractContextManager, contextmanager
from pathlib import Path
from typing import Any, TypeVar, cast, overload

import pytest
from _pytest.logging import LogCaptureHandler, _LiveLoggingNullHandler

from litestar._openapi.schema_generation import SchemaCreator
from litestar._openapi.schema_generation.plugins import openapi_schema_plugins
from litestar.openapi.spec import Schema
from litestar.plugins import OpenAPISchemaPluginProtocol
from litestar.typing import FieldDefinition

T = TypeVar("T")


RANDOM = random.Random(b"bA\xcd\x00\xa9$\xa7\x17\x1c\x10")


if sys.version_info >= (3, 12):
    getHandlerByName = logging.getHandlerByName
else:
    from logging import _handlers  # type: ignore[attr-defined]

    def getHandlerByName(name: str) -> Any:
        return _handlers.get(name)


@overload
async def maybe_async(obj: Awaitable[T]) -> T: ...


@overload
async def maybe_async(obj: T) -> T: ...


async def maybe_async(obj: Awaitable[T] | T) -> T:
    return await obj if inspect.isawaitable(obj) else obj  # pyright: ignore


class _AsyncContextManagerWrapper(AbstractAsyncContextManager):
    def __init__(self, cm: AbstractContextManager):
        self.cm = cm

    async def __aenter__(self) -> Any:
        return self.cm.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        return self.cm.__exit__(exc_type, exc_val, exc_tb)


def maybe_async_cm(obj: AbstractContextManager[T] | AbstractAsyncContextManager[T]) -> AbstractAsyncContextManager[T]:
    if isinstance(obj, AbstractContextManager):
        return cast(AbstractAsyncContextManager[T], _AsyncContextManagerWrapper(obj))
    return obj


def get_schema_for_field_definition(
    field_definition: FieldDefinition, *, plugins: list[OpenAPISchemaPluginProtocol] | None = None
) -> Schema:
    plugins = [*openapi_schema_plugins, *(plugins or [])]
    creator = SchemaCreator(plugins=plugins)
    result = creator.for_field_definition(field_definition)
    if isinstance(result, Schema):
        return result
    return creator.schema_registry.from_reference(result).schema


@contextmanager
def cleanup_logging_impl() -> Generator:
    # Reset root logger (`logging` module)
    std_root_logger: logging.Logger = logging.getLogger()
    for std_handler in std_root_logger.handlers:
        # Don't interfere with PyTest handler config
        if not isinstance(std_handler, (_LiveLoggingNullHandler, LogCaptureHandler)):
            std_root_logger.removeHandler(std_handler)
    picologging = pytest.importorskip("picologging")
    # Reset root logger (`picologging` module)
    pico_root_logger: picologging.Logger = picologging.getLogger()  # type: ignore[name-defined,unused-ignore] # pyright: ignore[reportPrivateUsage,reportGeneralTypeIssues,reportAssignmentType,reportInvalidTypeForm]
    for pico_handler in pico_root_logger.handlers:
        pico_root_logger.removeHandler(pico_handler)

    yield

    # Stop queue_listener listener (mandatory for the 'logging' module with Python 3.12,
    # else the test suite would hang on at the end of the tests and some tests would fail)
    queue_listener_handler = getHandlerByName("queue_listener")
    if queue_listener_handler and hasattr(queue_listener_handler, "listener"):
        atexit.unregister(queue_listener_handler.listener.stop)
        queue_listener_handler.listener.stop()
        queue_listener_handler.close()
        del queue_listener_handler


def not_none(val: T | None) -> T:
    assert val is not None
    return val


def purge_module(module_names: list[str], path: str | Path) -> None:
    for name in module_names:
        if name in sys.modules:
            del sys.modules[name]
    Path(importlib.util.cache_from_source(path)).unlink(missing_ok=True)  # type: ignore[arg-type]
