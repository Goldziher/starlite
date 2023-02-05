from functools import partial
from os import PathLike
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Dict,
    Iterable,
    Iterator,
    Literal,
    Mapping,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from starlite.enums import ScopeType

from .asgi_types import ASGIApp
from .callable_types import ExceptionHandler

if TYPE_CHECKING:
    from starlite.datastructures.cookie import Cookie
    from starlite.datastructures.response_header import ResponseHeader
    from starlite.datastructures.state import ImmutableState
    from starlite.di import Provide
    from starlite.middleware.base import DefineMiddleware, MiddlewareProtocol
    from starlite.params import ParameterKwarg
else:
    BaseHTTPMiddleware = Any
    Cookie = Any
    DefineMiddleware = Any
    ImmutableState = Any
    MiddlewareProtocol = Any
    ParameterKwarg = Any
    Provide = Any
    ResponseHeader = Any

T = TypeVar("T")


Dependencies = Mapping[str, Provide]
ExceptionHandlersMap = Mapping[Union[int, Type[Exception]], ExceptionHandler]
InitialStateType = Mapping[str, Any]
MaybePartial = Union[T, partial]
Middleware = Union[
    Callable[..., ASGIApp], DefineMiddleware, Iterator[Tuple[ASGIApp, Dict[str, Any]]], Type[MiddlewareProtocol]
]
ParametersMap = Mapping[str, ParameterKwarg]
PathType = Union[Path, PathLike, str]
ResponseCookies = Sequence[Cookie]
ResponseHeadersMap = Mapping[str, ResponseHeader]
Scopes = Set[Literal[ScopeType.HTTP, ScopeType.WEBSOCKET]]
StreamType = Union[Iterable[T], Iterator[T], AsyncIterable[T], AsyncIterator[T]]
TypeEncodersMap = Mapping[Any, Callable[[Any], Any]]
