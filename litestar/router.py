from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar._layers.utils import narrow_response_cookies, narrow_response_headers
from litestar.exceptions import ImproperlyConfiguredException
from litestar.types.empty import Empty
from litestar.utils import normalize_path
from litestar.utils.signature import add_types_to_signature_namespace
from litestar.utils.sync import ensure_async_callable

__all__ = ("Router",)


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from litestar.connection import Request, WebSocket
    from litestar.datastructures import CacheControlHeader, ETag
    from litestar.dto import AbstractDTO
    from litestar.openapi.spec import SecurityRequirement
    from litestar.response import Response
    from litestar.types import (
        AfterRequestHookHandler,
        AfterResponseHookHandler,
        BeforeRequestHookHandler,
        ControllerRouterHandler,
        ExceptionHandlersMap,
        Guard,
        Middleware,
        ParametersMap,
        ResponseCookies,
        TypeEncodersMap,
    )
    from litestar.types.callable_types import AsyncAfterRequestHookHandler, AsyncAfterResponseHookHandler
    from litestar.types.composite_types import Dependencies, ResponseHeaders, TypeDecodersSequence
    from litestar.types.empty import EmptyType


class Router:
    """The Litestar Router class.

    A Router instance is used to group controller, routers and route handler functions under a shared path fragment
    """

    __slots__ = (
        "after_request",
        "after_response",
        "before_request",
        "cache_control",
        "dependencies",
        "dto",
        "etag",
        "exception_handlers",
        "guards",
        "include_in_schema",
        "middleware",
        "opt",
        "parameters",
        "path",
        "registered_route_handler_ids",
        "request_class",
        "request_max_body_size",
        "response_class",
        "response_cookies",
        "response_headers",
        "return_dto",
        "route_handlers",
        "security",
        "signature_namespace",
        "tags",
        "type_decoders",
        "type_encoders",
        "websocket_class",
    )

    def __init__(
        self,
        path: str,
        *,
        after_request: AfterRequestHookHandler | None = None,
        after_response: AfterResponseHookHandler | None = None,
        before_request: BeforeRequestHookHandler | None = None,
        cache_control: CacheControlHeader | None = None,
        dependencies: Dependencies | None = None,
        dto: type[AbstractDTO] | None | EmptyType = Empty,
        etag: ETag | None = None,
        exception_handlers: ExceptionHandlersMap | None = None,
        guards: Sequence[Guard] | None = None,
        include_in_schema: bool | EmptyType = Empty,
        middleware: Sequence[Middleware] | None = None,
        opt: Mapping[str, Any] | None = None,
        parameters: ParametersMap | None = None,
        request_class: type[Request] | None = None,
        response_class: type[Response] | None = None,
        response_cookies: ResponseCookies | None = None,
        response_headers: ResponseHeaders | None = None,
        return_dto: type[AbstractDTO] | None | EmptyType = Empty,
        route_handlers: Sequence[ControllerRouterHandler],
        security: Sequence[SecurityRequirement] | None = None,
        signature_namespace: Mapping[str, Any] | None = None,
        signature_types: Sequence[Any] | None = None,
        tags: Sequence[str] | None = None,
        type_decoders: TypeDecodersSequence | None = None,
        type_encoders: TypeEncodersMap | None = None,
        websocket_class: type[WebSocket] | None = None,
        request_max_body_size: int | None | EmptyType = Empty,
    ) -> None:
        """Initialize a ``Router``.

        Args:
            after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
                to any route handler. If this function returns a value, the request will not reach the route handler,
                and instead this value will be used.
            after_response: A sync or async function called after the response has been awaited. It receives the
                :class:`Request <.connection.Request>` object and should not return any values.
            before_request: A sync or async function called immediately before calling the route handler. Receives
                the :class:`litestar.connection.Request` instance and any non-``None`` return value is used for the
                response, bypassing the route handler.
            cache_control: A ``cache-control`` header of type
                :class:`CacheControlHeader <.datastructures.CacheControlHeader>` to add to route handlers of
                this router. Can be overridden by route handlers.
            dependencies: A string keyed mapping of dependency :class:`Provide <.di.Provide>` instances.
            dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
                validation of request data.
            etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` to add to route handlers of this app.
            exception_handlers: A mapping of status codes and/or exception types to handler functions.
            guards: A sequence of :data:`Guard <.types.Guard>` callables.
            include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
            middleware: A sequence of :data:`Middleware <.types.Middleware>`.
            opt: A string keyed mapping of arbitrary values that can be accessed in :data:`Guards <.types.Guard>` or
                wherever you have access to :class:`Request <.connection.Request>` or
                :data:`ASGI Scope <.types.Scope>`.
            parameters: A mapping of :func:`Parameter <.params.Parameter>` definitions available to all application
                paths.
            path: A path fragment that is prefixed to all route handlers, controllers and other routers associated
                with the router instance.
            request_class: A custom subclass of :class:`Request <.connection.Request>` to be used as the default for
                all route handlers, controllers and other routers associated with the router instance.
            request_max_body_size: Maximum allowed size of the request body in bytes. If this size is exceeded,
                a '413 - Request Entity Too Large" error response is returned.
            response_class: A custom subclass of :class:`Response <.response.Response>` to be used as the default for
                all route handlers, controllers and other routers associated with the router instance.
            response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>` instances.
            response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
                instances.
            return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
                outbound response data.
            route_handlers: A required sequence of route handlers, which can include instances of
                :class:`Router <.router.Router>`, subclasses of :class:`Controller <.controller.Controller>` or any
                function decorated by the route handler decorators.
            security: A sequence of dicts that will be added to the schema of all route handlers in the application.
                See :data:`SecurityRequirement <.openapi.spec.SecurityRequirement>`
                for details.
            signature_namespace: A mapping of names to types for use in forward reference resolution during signature modeling.
            signature_types: A sequence of types for use in forward reference resolution during signature modeling.
                These types will be added to the signature namespace using their ``__name__`` attribute.
            tags: A sequence of string tags that will be appended to the schema of all route handlers under the
                application.
            type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec hook for deserialization.
            type_encoders: A mapping of types to callables that transform them into types supported for serialization.
            websocket_class: A custom subclass of :class:`WebSocket <.connection.WebSocket>` to be used as the default for
                all route handlers, controllers and other routers associated with the router instance.
        """

        self.after_request: AsyncAfterRequestHookHandler | None = (
            ensure_async_callable(after_request) if after_request else None  # type: ignore[assignment]
        )
        self.after_response: AsyncAfterResponseHookHandler | None = (
            ensure_async_callable(after_response) if after_response else None
        )
        self.before_request = ensure_async_callable(before_request) if before_request else None
        self.cache_control = cache_control
        self.dto = dto
        self.etag = etag
        self.dependencies = dict(dependencies or {})
        self.exception_handlers = dict(exception_handlers or {})
        self.guards = tuple(guards or [])
        self.include_in_schema = include_in_schema
        self.middleware = list(middleware or [])
        self.opt = dict(opt or {})
        self.parameters = dict(parameters or {})
        self.path = normalize_path(path)
        self.request_class = request_class
        self.response_class = response_class
        self.response_cookies = narrow_response_cookies(response_cookies) if response_cookies else ()
        self.response_headers = narrow_response_headers(response_headers) if response_headers else ()
        self.return_dto = return_dto
        self.security = list(security or [])
        self.signature_namespace = add_types_to_signature_namespace(
            signature_types or [], dict(signature_namespace or {})
        )
        self.tags = list(tags or [])
        self.registered_route_handler_ids: set[int] = set()
        self.type_encoders = dict(type_encoders) if type_encoders is not None else {}
        self.type_decoders = list(type_decoders) if type_decoders is not None else ()
        self.websocket_class = websocket_class
        self.request_max_body_size = request_max_body_size

        self.route_handlers = tuple(route_handlers)

    def register(self, value: ControllerRouterHandler) -> None:
        """Register a Controller, Route instance or RouteHandler on the router"""
        if value is self:
            raise ImproperlyConfiguredException("Cannot register a router on itself")
        self.route_handlers = (*self.route_handlers, value)
