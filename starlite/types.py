from typing import TYPE_CHECKING, Any, Awaitable, Callable, Type, TypeVar, Union

from pydantic.typing import AnyCallable
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import HTTPConnection
from starlette.responses import Response as StarletteResponse
from typing_extensions import Literal

from starlite.exceptions import HTTPException

if TYPE_CHECKING:
    from asgiref.typing import ASGI3Application as ASGIApp  # noqa: TC004
    from asgiref.typing import ASGIReceiveCallable as Receive  # noqa: TC004
    from asgiref.typing import ASGIReceiveEvent as Message  # noqa: TC004
    from asgiref.typing import ASGISendCallable as Send  # noqa: TC004
    from asgiref.typing import Scope  # noqa: TC004
    from starlette.middleware import Middleware as StarletteMiddleware  # noqa: TC004
    from starlette.middleware.base import BaseHTTPMiddleware  # noqa: TC004

    from starlite.connection import Request  # noqa: TC004
    from starlite.controller import Controller  # noqa: TC004
    from starlite.datastructures import State  # noqa: TC004
    from starlite.handlers import BaseRouteHandler  # noqa: TC004
    from starlite.middleware.base import (  # noqa: TC004
        DefineMiddleware,
        MiddlewareProtocol,
    )
    from starlite.response import Response  # noqa: TC004
    from starlite.router import Router  # noqa: TC004
else:
    ASGIApp = Any
    BaseHTTPMiddleware = Any
    BaseRouteHandler = Any
    Controller = Any
    DefineMiddleware = Any
    Message = Any
    MiddlewareProtocol = Any
    Receive = Any
    Request = Any
    Response = Any
    Router = Any
    Scope = Any
    Send = Any
    StarletteMiddleware = Any
    State = Any
    WebSocket = Any

H = TypeVar("H", bound=HTTPConnection)

Middleware = Union[
    StarletteMiddleware, DefineMiddleware, Type[BaseHTTPMiddleware], Type[MiddlewareProtocol], Callable[..., ASGIApp]
]

ExceptionHandler = Callable[
    [Request, Union[Exception, HTTPException, StarletteHTTPException]], Union[Response, StarletteResponse]
]
LifeCycleHandler = Union[
    Callable[[], Any],
    Callable[[State], Any],
    Callable[[], Awaitable[Any]],
    Callable[[State], Awaitable[Any]],
]
Guard = Union[Callable[[H, BaseRouteHandler], Awaitable[None]], Callable[[H, BaseRouteHandler], None]]
Method = Literal["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD"]
ReservedKwargs = Literal["request", "socket", "headers", "query", "cookies", "state", "data"]
ControllerRouterHandler = Union[Type[Controller], BaseRouteHandler, Router, AnyCallable]

# connection-lifecycle hook handlers
BeforeRequestHandler = Union[Callable[[Request], Any], Callable[[Request], Awaitable[Any]]]
AfterRequestHandler = Union[
    Callable[[Response], Response],
    Callable[[Response], Awaitable[Response]],
    Callable[[StarletteResponse], StarletteResponse],
    Callable[[StarletteResponse], Awaitable[StarletteResponse]],
]
AfterResponseHandler = Union[Callable[[Request], None], Callable[[Request], Awaitable[None]]]

AsyncAnyCallable = Callable[..., Awaitable[Any]]
CacheKeyBuilder = Callable[[Request], str]


class Empty:
    """A sentinel class used as placeholder."""


EmptyType = Type[Empty]

__all__ = [
    "ASGIApp",
    "AfterRequestHandler",
    "AfterResponseHandler",
    "AsyncAnyCallable",
    "BeforeRequestHandler",
    "CacheKeyBuilder",
    "ControllerRouterHandler",
    "Empty",
    "EmptyType",
    "ExceptionHandler",
    "Guard",
    "LifeCycleHandler",
    "Message",
    "Method",
    "Middleware",
    "Receive",
    "ReservedKwargs",
    "Scope",
    "Send",
]
