from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Generator
from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from litestar.app import Litestar
    from litestar.config.app import AppConfig
    from litestar.connection.base import ASGIConnection
    from litestar.connection.request import Request
    from litestar.handlers.base import BaseRouteHandler
    from litestar.handlers.http_handlers import HTTPRouteHandler
    from litestar.response.base import Response
    from litestar.types.asgi_types import ASGIApp, Message, Method, Scope
    from litestar.types.helper_types import SyncOrAsyncUnion
    from litestar.types.internal_types import PathParameterDefinition
    from litestar.types.protocols import Logger

ExceptionT = TypeVar("ExceptionT", bound=Exception)

AfterExceptionHookHandler: TypeAlias = "Callable[[ExceptionT, Scope], SyncOrAsyncUnion[None]]"
AsyncAfterRequestHookHandler: TypeAlias = (
    "Callable[[ASGIApp], Awaitable[ASGIApp]] | Callable[[Response], Awaitable[Response]]"
)
SyncAfterRequestHookHandler: TypeAlias = "Callable[[ASGIApp], ASGIApp] | Callable[[Response], Response]"
AfterRequestHookHandler: TypeAlias = "AsyncAfterRequestHookHandler | SyncAfterRequestHookHandler"

AsyncAfterResponseHookHandler: TypeAlias = "Callable[[Request], Awaitable[None]]"
SyncAfterResponseHookHandler: TypeAlias = "Callable[[Request], None]"
AfterResponseHookHandler: TypeAlias = "AsyncAfterResponseHookHandler | SyncAfterResponseHookHandler"

AsyncBeforeRequestHookHandler: TypeAlias = "Callable[[Request], Awaitable[Any]]"
BeforeRequestHookHandler: TypeAlias = "Callable[[Request], Any | Awaitable[Any]]"


AsyncAnyCallable: TypeAlias = Callable[..., Awaitable[Any]]
AnyCallable: TypeAlias = Callable[..., Any]
AnyGenerator: TypeAlias = "Generator[Any, Any, Any] | AsyncGenerator[Any, Any]"
BeforeMessageSendHookHandler: TypeAlias = "Callable[[Message, Scope], SyncOrAsyncUnion[None]]"
CacheKeyBuilder: TypeAlias = "Callable[[Request], str]"
ExceptionHandler: TypeAlias = "Callable[[Request, ExceptionT], Response]"
ExceptionLoggingHandler: TypeAlias = "Callable[[Logger, Scope, list[str]], None]"
GetLogger: TypeAlias = "Callable[..., Logger]"
AsyncGuard: TypeAlias = "Callable[[ASGIConnection, BaseRouteHandler], Awaitable[None]]"
SyncGuard: TypeAlias = "Callable[[ASGIConnection, BaseRouteHandler], None]"
Guard: TypeAlias = "AsyncGuard | SyncGuard"
LifespanHook: TypeAlias = "Callable[[Litestar], SyncOrAsyncUnion[Any]] | Callable[[], SyncOrAsyncUnion[Any]]"
OnAppInitHandler: TypeAlias = "Callable[[AppConfig], AppConfig]"
OperationIDCreator: TypeAlias = "Callable[[HTTPRouteHandler, Method, list[str | PathParameterDefinition]], str]"
Serializer: TypeAlias = Callable[[Any], Any]
HTTPHandlerDecorator: TypeAlias = "Callable[..., Callable[[AnyCallable], HTTPRouteHandler]]"
