from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Callable

from litestar.enums import HttpMethod, MediaType
from litestar.exceptions import HTTPException
from litestar.handlers.http_handlers.base import HTTPRouteHandler
from litestar.openapi.spec import Operation, SecurityRequirement
from litestar.types import (
    AfterRequestHookHandler,
    AfterResponseHookHandler,
    AnyCallable,
    BeforeRequestHookHandler,
    CacheKeyBuilder,
    Dependencies,
    Empty,
    EmptyType,
    ExceptionHandlersMap,
    Guard,
    Method,
    Middleware,
    OperationIDCreator,
    ResponseCookies,
    ResponseHeaders,
    TypeDecodersSequence,
    TypeEncodersMap,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

    from litestar.background_tasks import BackgroundTask, BackgroundTasks
    from litestar.config.response_cache import CACHE_FOREVER
    from litestar.connection import Request
    from litestar.datastructures import CacheControlHeader, ETag
    from litestar.dto import AbstractDTO
    from litestar.exceptions import HTTPException
    from litestar.openapi.datastructures import ResponseSpec
    from litestar.openapi.spec import SecurityRequirement
    from litestar.response import Response
    from litestar.types import (
        AfterRequestHookHandler,
        AfterResponseHookHandler,
        BeforeRequestHookHandler,
        CacheKeyBuilder,
        Dependencies,
        EmptyType,
        ExceptionHandlersMap,
        Guard,
        Middleware,
        ResponseCookies,
        ResponseHeaders,
        TypeEncodersMap,
    )
    from litestar.types.callable_types import AnyCallable, OperationIDCreator

__all__ = ("delete", "get", "head", "patch", "post", "put", "route")


def route(
    path: str | None | Sequence[str] = None,
    *,
    http_method: HttpMethod | Method | Sequence[HttpMethod | Method],
    after_request: AfterRequestHookHandler | None = None,
    after_response: AfterResponseHookHandler | None = None,
    background: BackgroundTask | BackgroundTasks | None = None,
    before_request: BeforeRequestHookHandler | None = None,
    cache: bool | int | type[CACHE_FOREVER] = False,
    cache_control: CacheControlHeader | None = None,
    cache_key_builder: CacheKeyBuilder | None = None,
    dependencies: Dependencies | None = None,
    dto: type[AbstractDTO] | None | EmptyType = Empty,
    etag: ETag | None = None,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    media_type: MediaType | str | None = None,
    middleware: Sequence[Middleware] | None = None,
    name: str | None = None,
    opt: Mapping[str, Any] | None = None,
    request_class: type[Request] | None = None,
    response_class: type[Response] | None = None,
    response_cookies: ResponseCookies | None = None,
    response_headers: ResponseHeaders | None = None,
    return_dto: type[AbstractDTO] | None | EmptyType = Empty,
    signature_namespace: Mapping[str, Any] | None = None,
    status_code: int | None = None,
    sync_to_thread: bool | None = None,
    # OpenAPI related attributes
    content_encoding: str | None = None,
    content_media_type: str | None = None,
    deprecated: bool = False,
    description: str | None = None,
    include_in_schema: bool | EmptyType = Empty,
    operation_class: type[Operation] = Operation,
    operation_id: str | OperationIDCreator | None = None,
    raises: Sequence[type[HTTPException]] | None = None,
    response_description: str | None = None,
    responses: Mapping[int, ResponseSpec] | None = None,
    security: Sequence[SecurityRequirement] | None = None,
    summary: str | None = None,
    tags: Sequence[str] | None = None,
    type_decoders: TypeDecodersSequence | None = None,
    type_encoders: TypeEncodersMap | None = None,
    handler_class: type[HTTPRouteHandler] = HTTPRouteHandler,
    **kwargs: Any,
) -> Callable[[AnyCallable], HTTPRouteHandler]:
    """Create an :class:`HTTPRouteHandler`.

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments.
            If not given defaults to ``/``
        after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
            to any route handler. If this function returns a value, the request will not reach the route handler,
            and instead this value will be used.
        after_response: A sync or async function called after the response has been awaited. It receives the
            :class:`Request <.connection.Request>` object and should not return any values.
        background: A :class:`BackgroundTask <.background_tasks.BackgroundTask>` instance or
            :class:`BackgroundTasks <.background_tasks.BackgroundTasks>` to execute after the response is finished.
            Defaults to ``None``.
        before_request: A sync or async function called immediately before calling the route handler. Receives
            the :class:`.connection.Request` instance and any non-``None`` return value is used for the response,
            bypassing the route handler.
        cache: Enables response caching if configured on the application level. Valid values are ``True`` or a number
            of seconds (e.g. ``120``) to cache the response.
        cache_control: A ``cache-control`` header of type
            :class:`CacheControlHeader <.datastructures.CacheControlHeader>` that will be added to the response.
        cache_key_builder: A :class:`cache-key builder function <.types.CacheKeyBuilder>`. Allows for customization
            of the cache key if caching is configured on the application level.
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
            validation of request data.
        etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` that will be added to the response.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        http_method: An :class:`http method string <.types.Method>`, a member of the enum
            :class:`HttpMethod <litestar.enums.HttpMethod>` or a list of these that correlates to the methods the
            route handler function should handle.
        media_type: A member of the :class:`MediaType <.enums.MediaType>` enum or a string with a
            valid IANA Media-Type.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or :class:`ASGI Scope <.types.Scope>`.
        request_class: A custom subclass of :class:`Request <.connection.Request>` to be used as route handler's
            default request.
        response_class: A custom subclass of :class:`Response <.response.Response>` to be used as route handler's
            default response.
        response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>` instances.
        response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
            instances.
        responses: A mapping of additional status codes and a description of their expected content.
            This information will be included in the OpenAPI schema
        return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
            outbound response data.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        status_code: An http status code for the response. Defaults to ``200`` for mixed method or ``GET``, ``PUT`` and
            ``PATCH``, ``201`` for ``POST`` and ``204`` for ``DELETE``.
        sync_to_thread: A boolean dictating whether the handler function will be executed in a worker thread or the
            main event loop. This has an effect only for sync handler functions. See using sync handler functions.
        content_encoding: A string describing the encoding of the content, e.g. ``base64``.
        content_media_type: A string designating the media-type of the content, e.g. ``image/png``.
        deprecated:  A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema.
        description: Text used for the route's schema description section.
        include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
        operation_class: :class:`Operation <.openapi.spec.operation.Operation>` to be used with the route's OpenAPI schema.
        operation_id: Either a string or a callable returning a string. An identifier used for the route's schema operationId.
        raises:  A list of exception classes extending from litestar.HttpException that is used for the OpenAPI documentation.
            This list should describe all exceptions raised within the route handler's function/method. The Litestar
            ValidationException will be added automatically for the schema if any validation is involved.
        response_description: Text used for the route's response schema description section.
        security: A sequence of dictionaries that contain information about which security scheme can be used on the endpoint.
        summary: Text used for the route's schema summary section.
        tags: A sequence of string tags that will be appended to the OpenAPI schema.
        type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec
            hook for deserialization.
        type_encoders: A mapping of types to callables that transform them into types supported for serialization.
        handler_class: Route handler class instantiated by the decorator

        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AnyCallable) -> HTTPRouteHandler:
        return handler_class(
            fn=fn,
            http_method=http_method,
            after_request=after_request,
            after_response=after_response,
            background=background,
            before_request=before_request,
            cache=cache,
            cache_control=cache_control,
            cache_key_builder=cache_key_builder,
            content_encoding=content_encoding,
            content_media_type=content_media_type,
            dependencies=dependencies,
            deprecated=deprecated,
            description=description,
            dto=dto,
            etag=etag,
            exception_handlers=exception_handlers,
            guards=guards,
            include_in_schema=include_in_schema,
            media_type=media_type,
            middleware=middleware,
            name=name,
            operation_class=operation_class,
            operation_id=operation_id,
            opt=opt,
            path=path,
            raises=raises,
            request_class=request_class,
            response_class=response_class,
            response_cookies=response_cookies,
            response_description=response_description,
            response_headers=response_headers,
            responses=responses,
            return_dto=return_dto,
            security=security,
            signature_namespace=signature_namespace,
            status_code=status_code,
            summary=summary,
            sync_to_thread=sync_to_thread,
            tags=tags,
            type_decoders=type_decoders,
            type_encoders=type_encoders,
            **kwargs,
        )

    return decorator


def get(
    path: str | None | Sequence[str] = None,
    *,
    after_request: AfterRequestHookHandler | None = None,
    after_response: AfterResponseHookHandler | None = None,
    background: BackgroundTask | BackgroundTasks | None = None,
    before_request: BeforeRequestHookHandler | None = None,
    cache: bool | int | type[CACHE_FOREVER] = False,
    cache_control: CacheControlHeader | None = None,
    cache_key_builder: CacheKeyBuilder | None = None,
    dependencies: Dependencies | None = None,
    dto: type[AbstractDTO] | None | EmptyType = Empty,
    etag: ETag | None = None,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    media_type: MediaType | str | None = None,
    middleware: Sequence[Middleware] | None = None,
    name: str | None = None,
    opt: Mapping[str, Any] | None = None,
    request_class: type[Request] | None = None,
    response_class: type[Response] | None = None,
    response_cookies: ResponseCookies | None = None,
    response_headers: ResponseHeaders | None = None,
    return_dto: type[AbstractDTO] | None | EmptyType = Empty,
    signature_namespace: Mapping[str, Any] | None = None,
    status_code: int | None = None,
    sync_to_thread: bool | None = None,
    # OpenAPI related attributes
    content_encoding: str | None = None,
    content_media_type: str | None = None,
    deprecated: bool = False,
    description: str | None = None,
    include_in_schema: bool | EmptyType = Empty,
    operation_class: type[Operation] = Operation,
    operation_id: str | OperationIDCreator | None = None,
    raises: Sequence[type[HTTPException]] | None = None,
    response_description: str | None = None,
    responses: Mapping[int, ResponseSpec] | None = None,
    security: Sequence[SecurityRequirement] | None = None,
    summary: str | None = None,
    tags: Sequence[str] | None = None,
    type_decoders: TypeDecodersSequence | None = None,
    type_encoders: TypeEncodersMap | None = None,
    handler_class: type[HTTPRouteHandler] = HTTPRouteHandler,
    **kwargs: Any,
) -> Callable[[AnyCallable], HTTPRouteHandler]:
    """Create an :class:`HTTPRouteHandler` with a ``GET`` method.

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments.
            If not given defaults to ``/``
        after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
            to any route handler. If this function returns a value, the request will not reach the route handler,
            and instead this value will be used.
        after_response: A sync or async function called after the response has been awaited. It receives the
            :class:`Request <.connection.Request>` object and should not return any values.
        background: A :class:`BackgroundTask <.background_tasks.BackgroundTask>` instance or
            :class:`BackgroundTasks <.background_tasks.BackgroundTasks>` to execute after the response is finished.
            Defaults to ``None``.
        before_request: A sync or async function called immediately before calling the route handler. Receives
            the :class:`.connection.Request` instance and any non-``None`` return value is used for the response,
            bypassing the route handler.
        cache: Enables response caching if configured on the application level. Valid values are ``True`` or a number
            of seconds (e.g. ``120``) to cache the response.
        cache_control: A ``cache-control`` header of type
            :class:`CacheControlHeader <.datastructures.CacheControlHeader>` that will be added to the response.
        cache_key_builder: A :class:`cache-key builder function <.types.CacheKeyBuilder>`. Allows for customization
            of the cache key if caching is configured on the application level.
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
            validation of request data.
        etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` that will be added to the response.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        media_type: A member of the :class:`MediaType <.enums.MediaType>` enum or a string with a
            valid IANA Media-Type.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or :class:`ASGI Scope <.types.Scope>`.
        request_class: A custom subclass of :class:`Request <.connection.Request>` to be used as route handler's
            default request.
        response_class: A custom subclass of :class:`Response <.response.Response>` to be used as route handler's
            default response.
        response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>` instances.
        response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
            instances.
        responses: A mapping of additional status codes and a description of their expected content.
            This information will be included in the OpenAPI schema
        return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
            outbound response data.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        status_code: An http status code for the response. Defaults to ``200`` for mixed method or ``GET``, ``PUT`` and
            ``PATCH``, ``201`` for ``POST`` and ``204`` for ``DELETE``.
        sync_to_thread: A boolean dictating whether the handler function will be executed in a worker thread or the
            main event loop. This has an effect only for sync handler functions. See using sync handler functions.
        content_encoding: A string describing the encoding of the content, e.g. ``base64``.
        content_media_type: A string designating the media-type of the content, e.g. ``image/png``.
        deprecated:  A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema.
        description: Text used for the route's schema description section.
        include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
        operation_class: :class:`Operation <.openapi.spec.operation.Operation>` to be used with the route's OpenAPI schema.
        operation_id: Either a string or a callable returning a string. An identifier used for the route's schema operationId.
        raises:  A list of exception classes extending from litestar.HttpException that is used for the OpenAPI documentation.
            This list should describe all exceptions raised within the route handler's function/method. The Litestar
            ValidationException will be added automatically for the schema if any validation is involved.
        response_description: Text used for the route's response schema description section.
        security: A sequence of dictionaries that contain information about which security scheme can be used on the endpoint.
        summary: Text used for the route's schema summary section.
        tags: A sequence of string tags that will be appended to the OpenAPI schema.
        type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec
            hook for deserialization.
        type_encoders: A mapping of types to callables that transform them into types supported for serialization.
        handler_class: Route handler class instantiated by the decorator

        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AnyCallable) -> HTTPRouteHandler:
        return handler_class(
            fn=fn,
            after_request=after_request,
            after_response=after_response,
            background=background,
            before_request=before_request,
            cache=cache,
            cache_control=cache_control,
            cache_key_builder=cache_key_builder,
            content_encoding=content_encoding,
            content_media_type=content_media_type,
            dependencies=dependencies,
            deprecated=deprecated,
            description=description,
            dto=dto,
            etag=etag,
            exception_handlers=exception_handlers,
            guards=guards,
            http_method=HttpMethod.GET,
            include_in_schema=include_in_schema,
            media_type=media_type,
            middleware=middleware,
            name=name,
            operation_class=operation_class,
            operation_id=operation_id,
            opt=opt,
            path=path,
            raises=raises,
            request_class=request_class,
            response_class=response_class,
            response_cookies=response_cookies,
            response_description=response_description,
            response_headers=response_headers,
            responses=responses,
            return_dto=return_dto,
            security=security,
            signature_namespace=signature_namespace,
            status_code=status_code,
            summary=summary,
            sync_to_thread=sync_to_thread,
            tags=tags,
            type_decoders=type_decoders,
            type_encoders=type_encoders,
            **kwargs,
        )

    return decorator


def head(
    path: str | None | Sequence[str] = None,
    *,
    after_request: AfterRequestHookHandler | None = None,
    after_response: AfterResponseHookHandler | None = None,
    background: BackgroundTask | BackgroundTasks | None = None,
    before_request: BeforeRequestHookHandler | None = None,
    cache: bool | int | type[CACHE_FOREVER] = False,
    cache_control: CacheControlHeader | None = None,
    cache_key_builder: CacheKeyBuilder | None = None,
    dependencies: Dependencies | None = None,
    dto: type[AbstractDTO] | None | EmptyType = Empty,
    etag: ETag | None = None,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    media_type: MediaType | str | None = None,
    middleware: Sequence[Middleware] | None = None,
    name: str | None = None,
    opt: Mapping[str, Any] | None = None,
    request_class: type[Request] | None = None,
    response_class: type[Response] | None = None,
    response_cookies: ResponseCookies | None = None,
    response_headers: ResponseHeaders | None = None,
    signature_namespace: Mapping[str, Any] | None = None,
    status_code: int | None = None,
    sync_to_thread: bool | None = None,
    # OpenAPI related attributes
    content_encoding: str | None = None,
    content_media_type: str | None = None,
    deprecated: bool = False,
    description: str | None = None,
    include_in_schema: bool | EmptyType = Empty,
    operation_class: type[Operation] = Operation,
    operation_id: str | OperationIDCreator | None = None,
    raises: Sequence[type[HTTPException]] | None = None,
    response_description: str | None = None,
    responses: Mapping[int, ResponseSpec] | None = None,
    return_dto: type[AbstractDTO] | None | EmptyType = Empty,
    security: Sequence[SecurityRequirement] | None = None,
    summary: str | None = None,
    tags: Sequence[str] | None = None,
    type_decoders: TypeDecodersSequence | None = None,
    type_encoders: TypeEncodersMap | None = None,
    handler_class: type[HTTPRouteHandler] = HTTPRouteHandler,
    **kwargs: Any,
) -> Callable[[AnyCallable], HTTPRouteHandler]:
    """Create an :class:`HTTPRouteHandler` with a ``HEAD`` method.

    Notes:
        - A response to a head request cannot include a body.
            See: [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/HEAD).

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments.
            If not given defaults to ``/``
        after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
            to any route handler. If this function returns a value, the request will not reach the route handler,
            and instead this value will be used.
        after_response: A sync or async function called after the response has been awaited. It receives the
            :class:`Request <.connection.Request>` object and should not return any values.
        background: A :class:`BackgroundTask <.background_tasks.BackgroundTask>` instance or
            :class:`BackgroundTasks <.background_tasks.BackgroundTasks>` to execute after the response is finished.
            Defaults to ``None``.
        before_request: A sync or async function called immediately before calling the route handler. Receives
            the :class:`.connection.Request` instance and any non-``None`` return value is used for the response,
            bypassing the route handler.
        cache: Enables response caching if configured on the application level. Valid values are ``True`` or a number
            of seconds (e.g. ``120``) to cache the response.
        cache_control: A ``cache-control`` header of type
            :class:`CacheControlHeader <.datastructures.CacheControlHeader>` that will be added to the response.
        cache_key_builder: A :class:`cache-key builder function <.types.CacheKeyBuilder>`. Allows for customization
            of the cache key if caching is configured on the application level.
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
            validation of request data.
        etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` that will be added to the response.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        media_type: A member of the :class:`MediaType <.enums.MediaType>` enum or a string with a
            valid IANA Media-Type.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or :class:`ASGI Scope <.types.Scope>`.
        request_class: A custom subclass of :class:`Request <.connection.Request>` to be used as route handler's
            default request.
        response_class: A custom subclass of :class:`Response <.response.Response>` to be used as route handler's
            default response.
        response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>` instances.
        response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
            instances.
        responses: A mapping of additional status codes and a description of their expected content.
            This information will be included in the OpenAPI schema
        return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
            outbound response data.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        status_code: An http status code for the response. Defaults to ``200`` for mixed method or ``GET``, ``PUT`` and
            ``PATCH``, ``201`` for ``POST`` and ``204`` for ``DELETE``.
        sync_to_thread: A boolean dictating whether the handler function will be executed in a worker thread or the
            main event loop. This has an effect only for sync handler functions. See using sync handler functions.
        content_encoding: A string describing the encoding of the content, e.g. ``base64``.
        content_media_type: A string designating the media-type of the content, e.g. ``image/png``.
        deprecated:  A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema.
        description: Text used for the route's schema description section.
        include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
        operation_class: :class:`Operation <.openapi.spec.operation.Operation>` to be used with the route's OpenAPI schema.
        operation_id: Either a string or a callable returning a string. An identifier used for the route's schema operationId.
        raises:  A list of exception classes extending from litestar.HttpException that is used for the OpenAPI documentation.
            This list should describe all exceptions raised within the route handler's function/method. The Litestar
            ValidationException will be added automatically for the schema if any validation is involved.
        response_description: Text used for the route's response schema description section.
        security: A sequence of dictionaries that contain information about which security scheme can be used on the endpoint.
        summary: Text used for the route's schema summary section.
        tags: A sequence of string tags that will be appended to the OpenAPI schema.
        type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec
            hook for deserialization.
        type_encoders: A mapping of types to callables that transform them into types supported for serialization.
        handler_class: Route handler class instantiated by the decorator

        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AnyCallable) -> HTTPRouteHandler:
        return handler_class(
            fn=fn,
            after_request=after_request,
            after_response=after_response,
            background=background,
            before_request=before_request,
            cache=cache,
            cache_control=cache_control,
            cache_key_builder=cache_key_builder,
            content_encoding=content_encoding,
            content_media_type=content_media_type,
            dependencies=dependencies,
            deprecated=deprecated,
            description=description,
            dto=dto,
            etag=etag,
            exception_handlers=exception_handlers,
            guards=guards,
            http_method=HttpMethod.HEAD,
            include_in_schema=include_in_schema,
            media_type=media_type,
            middleware=middleware,
            name=name,
            operation_class=operation_class,
            operation_id=operation_id,
            opt=opt,
            path=path,
            raises=raises,
            request_class=request_class,
            response_class=response_class,
            response_cookies=response_cookies,
            response_description=response_description,
            response_headers=response_headers,
            responses=responses,
            return_dto=return_dto,
            security=security,
            signature_namespace=signature_namespace,
            status_code=status_code,
            summary=summary,
            sync_to_thread=sync_to_thread,
            tags=tags,
            type_decoders=type_decoders,
            type_encoders=type_encoders,
            **kwargs,
        )

    return decorator


def patch(
    path: str | None | Sequence[str] = None,
    *,
    after_request: AfterRequestHookHandler | None = None,
    after_response: AfterResponseHookHandler | None = None,
    background: BackgroundTask | BackgroundTasks | None = None,
    before_request: BeforeRequestHookHandler | None = None,
    cache: bool | int | type[CACHE_FOREVER] = False,
    cache_control: CacheControlHeader | None = None,
    cache_key_builder: CacheKeyBuilder | None = None,
    dependencies: Dependencies | None = None,
    dto: type[AbstractDTO] | None | EmptyType = Empty,
    etag: ETag | None = None,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    media_type: MediaType | str | None = None,
    middleware: Sequence[Middleware] | None = None,
    name: str | None = None,
    opt: Mapping[str, Any] | None = None,
    request_class: type[Request] | None = None,
    request_max_body_size: int | None | EmptyType = Empty,
    response_class: type[Response] | None = None,
    response_cookies: ResponseCookies | None = None,
    response_headers: ResponseHeaders | None = None,
    return_dto: type[AbstractDTO] | None | EmptyType = Empty,
    signature_namespace: Mapping[str, Any] | None = None,
    status_code: int | None = None,
    sync_to_thread: bool | None = None,
    # OpenAPI related attributes
    content_encoding: str | None = None,
    content_media_type: str | None = None,
    deprecated: bool = False,
    description: str | None = None,
    include_in_schema: bool | EmptyType = Empty,
    operation_class: type[Operation] = Operation,
    operation_id: str | OperationIDCreator | None = None,
    raises: Sequence[type[HTTPException]] | None = None,
    response_description: str | None = None,
    responses: Mapping[int, ResponseSpec] | None = None,
    security: Sequence[SecurityRequirement] | None = None,
    summary: str | None = None,
    tags: Sequence[str] | None = None,
    type_decoders: TypeDecodersSequence | None = None,
    type_encoders: TypeEncodersMap | None = None,
    handler_class: type[HTTPRouteHandler] = HTTPRouteHandler,
    **kwargs: Any,
) -> Callable[[AnyCallable], HTTPRouteHandler]:
    """Create an :class:`HTTPRouteHandler` with a ``PATCH`` method.

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments.
            If not given defaults to ``/``
        after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
            to any route handler. If this function returns a value, the request will not reach the route handler,
            and instead this value will be used.
        after_response: A sync or async function called after the response has been awaited. It receives the
            :class:`Request <.connection.Request>` object and should not return any values.
        background: A :class:`BackgroundTask <.background_tasks.BackgroundTask>` instance or
            :class:`BackgroundTasks <.background_tasks.BackgroundTasks>` to execute after the response is finished.
            Defaults to ``None``.
        before_request: A sync or async function called immediately before calling the route handler. Receives
            the :class:`.connection.Request` instance and any non-``None`` return value is used for the response,
            bypassing the route handler.
        cache: Enables response caching if configured on the application level. Valid values are ``True`` or a number
            of seconds (e.g. ``120``) to cache the response.
        cache_control: A ``cache-control`` header of type
            :class:`CacheControlHeader <.datastructures.CacheControlHeader>` that will be added to the response.
        cache_key_builder: A :class:`cache-key builder function <.types.CacheKeyBuilder>`. Allows for customization
            of the cache key if caching is configured on the application level.
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
            validation of request data.
        etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` that will be added to the response.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        media_type: A member of the :class:`MediaType <.enums.MediaType>` enum or a string with a
            valid IANA Media-Type.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or :class:`ASGI Scope <.types.Scope>`.
        request_class: A custom subclass of :class:`Request <.connection.Request>` to be used as route handler's
            default request.
        request_max_body_size: Maximum allowed size of the request body in bytes. If this size is exceeded,
                a '413 - Request Entity Too Large' error response is returned.
        response_class: A custom subclass of :class:`Response <.response.Response>` to be used as route handler's
            default response.
        response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>` instances.
        response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
            instances.
        responses: A mapping of additional status codes and a description of their expected content.
            This information will be included in the OpenAPI schema
        return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
            outbound response data.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        status_code: An http status code for the response. Defaults to ``200`` for mixed method or ``GET``, ``PUT`` and
            ``PATCH``, ``201`` for ``POST`` and ``204`` for ``DELETE``.
        sync_to_thread: A boolean dictating whether the handler function will be executed in a worker thread or the
            main event loop. This has an effect only for sync handler functions. See using sync handler functions.
        content_encoding: A string describing the encoding of the content, e.g. ``base64``.
        content_media_type: A string designating the media-type of the content, e.g. ``image/png``.
        deprecated:  A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema.
        description: Text used for the route's schema description section.
        include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
        operation_class: :class:`Operation <.openapi.spec.operation.Operation>` to be used with the route's OpenAPI schema.
        operation_id: Either a string or a callable returning a string. An identifier used for the route's schema operationId.
        raises:  A list of exception classes extending from litestar.HttpException that is used for the OpenAPI documentation.
            This list should describe all exceptions raised within the route handler's function/method. The Litestar
            ValidationException will be added automatically for the schema if any validation is involved.
        response_description: Text used for the route's response schema description section.
        security: A sequence of dictionaries that contain information about which security scheme can be used on the endpoint.
        summary: Text used for the route's schema summary section.
        tags: A sequence of string tags that will be appended to the OpenAPI schema.
        type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec
            hook for deserialization.
        type_encoders: A mapping of types to callables that transform them into types supported for serialization.
        handler_class: Route handler class instantiated by the decorator

        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AnyCallable) -> HTTPRouteHandler:
        return handler_class(
            fn=fn,
            after_request=after_request,
            after_response=after_response,
            background=background,
            before_request=before_request,
            cache=cache,
            cache_control=cache_control,
            cache_key_builder=cache_key_builder,
            content_encoding=content_encoding,
            content_media_type=content_media_type,
            dependencies=dependencies,
            deprecated=deprecated,
            description=description,
            dto=dto,
            etag=etag,
            exception_handlers=exception_handlers,
            guards=guards,
            http_method=HttpMethod.PATCH,
            include_in_schema=include_in_schema,
            media_type=media_type,
            middleware=middleware,
            name=name,
            operation_class=operation_class,
            operation_id=operation_id,
            opt=opt,
            path=path,
            raises=raises,
            request_class=request_class,
            request_max_body_size=request_max_body_size,
            response_class=response_class,
            response_cookies=response_cookies,
            response_description=response_description,
            response_headers=response_headers,
            responses=responses,
            return_dto=return_dto,
            security=security,
            signature_namespace=signature_namespace,
            status_code=status_code,
            summary=summary,
            sync_to_thread=sync_to_thread,
            tags=tags,
            type_decoders=type_decoders,
            type_encoders=type_encoders,
            **kwargs,
        )

    return decorator


def post(
    path: str | None | Sequence[str] = None,
    *,
    after_request: AfterRequestHookHandler | None = None,
    after_response: AfterResponseHookHandler | None = None,
    background: BackgroundTask | BackgroundTasks | None = None,
    before_request: BeforeRequestHookHandler | None = None,
    cache: bool | int | type[CACHE_FOREVER] = False,
    cache_control: CacheControlHeader | None = None,
    cache_key_builder: CacheKeyBuilder | None = None,
    dependencies: Dependencies | None = None,
    dto: type[AbstractDTO] | None | EmptyType = Empty,
    etag: ETag | None = None,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    media_type: MediaType | str | None = None,
    middleware: Sequence[Middleware] | None = None,
    name: str | None = None,
    opt: Mapping[str, Any] | None = None,
    request_class: type[Request] | None = None,
    request_max_body_size: int | None | EmptyType = Empty,
    response_class: type[Response] | None = None,
    response_cookies: ResponseCookies | None = None,
    response_headers: ResponseHeaders | None = None,
    return_dto: type[AbstractDTO] | None | EmptyType = Empty,
    signature_namespace: Mapping[str, Any] | None = None,
    status_code: int | None = None,
    sync_to_thread: bool | None = None,
    # OpenAPI related attributes
    content_encoding: str | None = None,
    content_media_type: str | None = None,
    deprecated: bool = False,
    description: str | None = None,
    include_in_schema: bool | EmptyType = Empty,
    operation_class: type[Operation] = Operation,
    operation_id: str | OperationIDCreator | None = None,
    raises: Sequence[type[HTTPException]] | None = None,
    response_description: str | None = None,
    responses: Mapping[int, ResponseSpec] | None = None,
    security: Sequence[SecurityRequirement] | None = None,
    summary: str | None = None,
    tags: Sequence[str] | None = None,
    type_decoders: TypeDecodersSequence | None = None,
    type_encoders: TypeEncodersMap | None = None,
    handler_class: type[HTTPRouteHandler] = HTTPRouteHandler,
    **kwargs: Any,
) -> Callable[[AnyCallable], HTTPRouteHandler]:
    """Create an :class:`HTTPRouteHandler` with a ``POST`` method.

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments.
            If not given defaults to ``/``
        after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
            to any route handler. If this function returns a value, the request will not reach the route handler,
            and instead this value will be used.
        after_response: A sync or async function called after the response has been awaited. It receives the
            :class:`Request <.connection.Request>` object and should not return any values.
        background: A :class:`BackgroundTask <.background_tasks.BackgroundTask>` instance or
            :class:`BackgroundTasks <.background_tasks.BackgroundTasks>` to execute after the response is finished.
            Defaults to ``None``.
        before_request: A sync or async function called immediately before calling the route handler. Receives
            the :class:`.connection.Request` instance and any non-``None`` return value is used for the response,
            bypassing the route handler.
        cache: Enables response caching if configured on the application level. Valid values are ``True`` or a number
            of seconds (e.g. ``120``) to cache the response.
        cache_control: A ``cache-control`` header of type
            :class:`CacheControlHeader <.datastructures.CacheControlHeader>` that will be added to the response.
        cache_key_builder: A :class:`cache-key builder function <.types.CacheKeyBuilder>`. Allows for customization
            of the cache key if caching is configured on the application level.
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
            validation of request data.
        etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` that will be added to the response.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        media_type: A member of the :class:`MediaType <.enums.MediaType>` enum or a string with a
            valid IANA Media-Type.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or :class:`ASGI Scope <.types.Scope>`.
        request_class: A custom subclass of :class:`Request <.connection.Request>` to be used as route handler's
            default request.
        request_max_body_size: Maximum allowed size of the request body in bytes. If this size is exceeded,
                a '413 - Request Entity Too Large' error response is returned.
        response_class: A custom subclass of :class:`Response <.response.Response>` to be used as route handler's
            default response.
        response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>` instances.
        response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
            instances.
        responses: A mapping of additional status codes and a description of their expected content.
            This information will be included in the OpenAPI schema
        return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
            outbound response data.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        status_code: An http status code for the response. Defaults to ``200`` for mixed method or ``GET``, ``PUT`` and
            ``PATCH``, ``201`` for ``POST`` and ``204`` for ``DELETE``.
        sync_to_thread: A boolean dictating whether the handler function will be executed in a worker thread or the
            main event loop. This has an effect only for sync handler functions. See using sync handler functions.
        content_encoding: A string describing the encoding of the content, e.g. ``base64``.
        content_media_type: A string designating the media-type of the content, e.g. ``image/png``.
        deprecated:  A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema.
        description: Text used for the route's schema description section.
        include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
        operation_class: :class:`Operation <.openapi.spec.operation.Operation>` to be used with the route's OpenAPI schema.
        operation_id: Either a string or a callable returning a string. An identifier used for the route's schema operationId.
        raises:  A list of exception classes extending from litestar.HttpException that is used for the OpenAPI documentation.
            This list should describe all exceptions raised within the route handler's function/method. The Litestar
            ValidationException will be added automatically for the schema if any validation is involved.
        response_description: Text used for the route's response schema description section.
        security: A sequence of dictionaries that contain information about which security scheme can be used on the endpoint.
        summary: Text used for the route's schema summary section.
        tags: A sequence of string tags that will be appended to the OpenAPI schema.
        type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec
            hook for deserialization.
        type_encoders: A mapping of types to callables that transform them into types supported for serialization.
        handler_class: Route handler class instantiated by the decorator

        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AnyCallable) -> HTTPRouteHandler:
        return handler_class(
            fn=fn,
            after_request=after_request,
            after_response=after_response,
            background=background,
            before_request=before_request,
            cache=cache,
            cache_control=cache_control,
            cache_key_builder=cache_key_builder,
            content_encoding=content_encoding,
            content_media_type=content_media_type,
            dependencies=dependencies,
            deprecated=deprecated,
            description=description,
            dto=dto,
            exception_handlers=exception_handlers,
            etag=etag,
            guards=guards,
            http_method=HttpMethod.POST,
            include_in_schema=include_in_schema,
            media_type=media_type,
            middleware=middleware,
            name=name,
            operation_class=operation_class,
            operation_id=operation_id,
            opt=opt,
            path=path,
            raises=raises,
            request_class=request_class,
            request_max_body_size=request_max_body_size,
            response_class=response_class,
            response_cookies=response_cookies,
            response_description=response_description,
            response_headers=response_headers,
            responses=responses,
            return_dto=return_dto,
            signature_namespace=signature_namespace,
            security=security,
            status_code=status_code,
            summary=summary,
            sync_to_thread=sync_to_thread,
            tags=tags,
            type_decoders=type_decoders,
            type_encoders=type_encoders,
            **kwargs,
        )

    return decorator


def put(
    path: str | None | Sequence[str] = None,
    *,
    after_request: AfterRequestHookHandler | None = None,
    after_response: AfterResponseHookHandler | None = None,
    background: BackgroundTask | BackgroundTasks | None = None,
    before_request: BeforeRequestHookHandler | None = None,
    cache: bool | int | type[CACHE_FOREVER] = False,
    cache_control: CacheControlHeader | None = None,
    cache_key_builder: CacheKeyBuilder | None = None,
    dependencies: Dependencies | None = None,
    dto: type[AbstractDTO] | None | EmptyType = Empty,
    etag: ETag | None = None,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    media_type: MediaType | str | None = None,
    middleware: Sequence[Middleware] | None = None,
    name: str | None = None,
    opt: Mapping[str, Any] | None = None,
    request_class: type[Request] | None = None,
    request_max_body_size: int | None | EmptyType = Empty,
    response_class: type[Response] | None = None,
    response_cookies: ResponseCookies | None = None,
    response_headers: ResponseHeaders | None = None,
    return_dto: type[AbstractDTO] | None | EmptyType = Empty,
    signature_namespace: Mapping[str, Any] | None = None,
    status_code: int | None = None,
    sync_to_thread: bool | None = None,
    # OpenAPI related attributes
    content_encoding: str | None = None,
    content_media_type: str | None = None,
    deprecated: bool = False,
    description: str | None = None,
    include_in_schema: bool | EmptyType = Empty,
    operation_class: type[Operation] = Operation,
    operation_id: str | OperationIDCreator | None = None,
    raises: Sequence[type[HTTPException]] | None = None,
    response_description: str | None = None,
    responses: Mapping[int, ResponseSpec] | None = None,
    security: Sequence[SecurityRequirement] | None = None,
    summary: str | None = None,
    tags: Sequence[str] | None = None,
    type_decoders: TypeDecodersSequence | None = None,
    type_encoders: TypeEncodersMap | None = None,
    handler_class: type[HTTPRouteHandler] = HTTPRouteHandler,
    **kwargs: Any,
) -> Callable[[AnyCallable], HTTPRouteHandler]:
    """Create an :class:`HTTPRouteHandler` with a ``PUT`` method.

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments.
            If not given defaults to ``/``
        after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
            to any route handler. If this function returns a value, the request will not reach the route handler,
            and instead this value will be used.
        after_response: A sync or async function called after the response has been awaited. It receives the
            :class:`Request <.connection.Request>` object and should not return any values.
        background: A :class:`BackgroundTask <.background_tasks.BackgroundTask>` instance or
            :class:`BackgroundTasks <.background_tasks.BackgroundTasks>` to execute after the response is finished.
            Defaults to ``None``.
        before_request: A sync or async function called immediately before calling the route handler. Receives
            the :class:`.connection.Request` instance and any non-``None`` return value is used for the response,
            bypassing the route handler.
        cache: Enables response caching if configured on the application level. Valid values are ``True`` or a number
            of seconds (e.g. ``120``) to cache the response.
        cache_control: A ``cache-control`` header of type
            :class:`CacheControlHeader <.datastructures.CacheControlHeader>` that will be added to the response.
        cache_key_builder: A :class:`cache-key builder function <.types.CacheKeyBuilder>`. Allows for customization
            of the cache key if caching is configured on the application level.
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
            validation of request data.
        etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` that will be added to the response.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        media_type: A member of the :class:`MediaType <.enums.MediaType>` enum or a string with a
            valid IANA Media-Type.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or :class:`ASGI Scope <.types.Scope>`.
        request_class: A custom subclass of :class:`Request <.connection.Request>` to be used as route handler's
            default request.
        request_max_body_size: Maximum allowed size of the request body in bytes. If this size is exceeded,
                a '413 - Request Entity Too Large' error response is returned.
        response_class: A custom subclass of :class:`Response <.response.Response>` to be used as route handler's
            default response.
        response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>` instances.
        response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
            instances.
        responses: A mapping of additional status codes and a description of their expected content.
            This information will be included in the OpenAPI schema
        return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
            outbound response data.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        status_code: An http status code for the response. Defaults to ``200`` for mixed method or ``GET``, ``PUT`` and
            ``PATCH``, ``201`` for ``POST`` and ``204`` for ``DELETE``.
        sync_to_thread: A boolean dictating whether the handler function will be executed in a worker thread or the
            main event loop. This has an effect only for sync handler functions. See using sync handler functions.
        content_encoding: A string describing the encoding of the content, e.g. ``base64``.
        content_media_type: A string designating the media-type of the content, e.g. ``image/png``.
        deprecated:  A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema.
        description: Text used for the route's schema description section.
        include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
        operation_class: :class:`Operation <.openapi.spec.operation.Operation>` to be used with the route's OpenAPI schema.
        operation_id: Either a string or a callable returning a string. An identifier used for the route's schema operationId.
        raises:  A list of exception classes extending from litestar.HttpException that is used for the OpenAPI documentation.
            This list should describe all exceptions raised within the route handler's function/method. The Litestar
            ValidationException will be added automatically for the schema if any validation is involved.
        response_description: Text used for the route's response schema description section.
        security: A sequence of dictionaries that contain information about which security scheme can be used on the endpoint.
        summary: Text used for the route's schema summary section.
        tags: A sequence of string tags that will be appended to the OpenAPI schema.
        type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec
            hook for deserialization.
        type_encoders: A mapping of types to callables that transform them into types supported for serialization.
        handler_class: Route handler class instantiated by the decorator
        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AnyCallable) -> HTTPRouteHandler:
        return handler_class(
            fn=fn,
            after_request=after_request,
            after_response=after_response,
            background=background,
            before_request=before_request,
            cache=cache,
            cache_control=cache_control,
            cache_key_builder=cache_key_builder,
            content_encoding=content_encoding,
            content_media_type=content_media_type,
            dependencies=dependencies,
            deprecated=deprecated,
            description=description,
            dto=dto,
            exception_handlers=exception_handlers,
            etag=etag,
            guards=guards,
            http_method=HttpMethod.PUT,
            include_in_schema=include_in_schema,
            media_type=media_type,
            middleware=middleware,
            name=name,
            operation_class=operation_class,
            operation_id=operation_id,
            opt=opt,
            path=path,
            raises=raises,
            request_class=request_class,
            request_max_body_size=request_max_body_size,
            response_class=response_class,
            response_cookies=response_cookies,
            response_description=response_description,
            response_headers=response_headers,
            responses=responses,
            return_dto=return_dto,
            security=security,
            signature_namespace=signature_namespace,
            status_code=status_code,
            summary=summary,
            sync_to_thread=sync_to_thread,
            tags=tags,
            type_decoders=type_decoders,
            type_encoders=type_encoders,
            **kwargs,
        )

    return decorator


def delete(
    path: str | None | Sequence[str] = None,
    *,
    after_request: AfterRequestHookHandler | None = None,
    after_response: AfterResponseHookHandler | None = None,
    background: BackgroundTask | BackgroundTasks | None = None,
    before_request: BeforeRequestHookHandler | None = None,
    cache: bool | int | type[CACHE_FOREVER] = False,
    cache_control: CacheControlHeader | None = None,
    cache_key_builder: CacheKeyBuilder | None = None,
    dependencies: Dependencies | None = None,
    dto: type[AbstractDTO] | None | EmptyType = Empty,
    etag: ETag | None = None,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    media_type: MediaType | str | None = None,
    middleware: Sequence[Middleware] | None = None,
    name: str | None = None,
    opt: Mapping[str, Any] | None = None,
    request_class: type[Request] | None = None,
    response_class: type[Response] | None = None,
    response_cookies: ResponseCookies | None = None,
    response_headers: ResponseHeaders | None = None,
    return_dto: type[AbstractDTO] | None | EmptyType = Empty,
    signature_namespace: Mapping[str, Any] | None = None,
    status_code: int | None = None,
    sync_to_thread: bool | None = None,
    # OpenAPI related attributes
    content_encoding: str | None = None,
    content_media_type: str | None = None,
    deprecated: bool = False,
    description: str | None = None,
    include_in_schema: bool | EmptyType = Empty,
    operation_class: type[Operation] = Operation,
    operation_id: str | OperationIDCreator | None = None,
    raises: Sequence[type[HTTPException]] | None = None,
    response_description: str | None = None,
    responses: Mapping[int, ResponseSpec] | None = None,
    security: Sequence[SecurityRequirement] | None = None,
    summary: str | None = None,
    tags: Sequence[str] | None = None,
    type_decoders: TypeDecodersSequence | None = None,
    type_encoders: TypeEncodersMap | None = None,
    handler_class: type[HTTPRouteHandler] = HTTPRouteHandler,
    **kwargs: Any,
) -> Callable[[AnyCallable], HTTPRouteHandler]:
    """Create an :class:`HTTPRouteHandler` with a ``DELETE`` method.

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments.
            If not given defaults to ``/``
        after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
            to any route handler. If this function returns a value, the request will not reach the route handler,
            and instead this value will be used.
        after_response: A sync or async function called after the response has been awaited. It receives the
            :class:`Request <.connection.Request>` object and should not return any values.
        background: A :class:`BackgroundTask <.background_tasks.BackgroundTask>` instance or
            :class:`BackgroundTasks <.background_tasks.BackgroundTasks>` to execute after the response is finished.
            Defaults to ``None``.
        before_request: A sync or async function called immediately before calling the route handler. Receives
            the :class:`.connection.Request` instance and any non-``None`` return value is used for the response,
            bypassing the route handler.
        cache: Enables response caching if configured on the application level. Valid values are ``True`` or a number
            of seconds (e.g. ``120``) to cache the response.
        cache_control: A ``cache-control`` header of type
            :class:`CacheControlHeader <.datastructures.CacheControlHeader>` that will be added to the response.
        cache_key_builder: A :class:`cache-key builder function <.types.CacheKeyBuilder>`. Allows for customization
            of the cache key if caching is configured on the application level.
        dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
            validation of request data.
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` that will be added to the response.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        media_type: A member of the :class:`MediaType <.enums.MediaType>` enum or a string with a
            valid IANA Media-Type.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or :class:`ASGI Scope <.types.Scope>`.
        request_class: A custom subclass of :class:`Request <.connection.Request>` to be used as route handler's
            default request.
        response_class: A custom subclass of :class:`Response <.response.Response>` to be used as route handler's
            default response.
        response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>` instances.
        response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
            instances.
        responses: A mapping of additional status codes and a description of their expected content.
            This information will be included in the OpenAPI schema
        return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
            outbound response data.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        status_code: An http status code for the response. Defaults to ``200`` for mixed method or ``GET``, ``PUT``
            and ``PATCH``, ``201`` for ``POST`` and ``204`` for ``DELETE``.
        sync_to_thread: A boolean dictating whether the handler function will be executed in a worker thread or the
            main event loop. This has an effect only for sync handler functions. See using sync handler functions.
        content_encoding: A string describing the encoding of the content, e.g. ``base64``.
        content_media_type: A string designating the media-type of the content, e.g. ``image/png``.
        deprecated:  A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema.
        description: Text used for the route's schema description section.
        include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
        operation_class: :class:`Operation <.openapi.spec.operation.Operation>` to be used with the route's OpenAPI schema.
        operation_id: Either a string or a callable returning a string. An identifier used for the route's schema operationId.
        raises:  A list of exception classes extending from litestar.HttpException that is used for the OpenAPI documentation.
            This list should describe all exceptions raised within the route handler's function/method. The Litestar
            ValidationException will be added automatically for the schema if any validation is involved.
        response_description: Text used for the route's response schema description section.
        security: A sequence of dictionaries that contain information about which security scheme can be used on the endpoint.
        summary: Text used for the route's schema summary section.
        tags: A sequence of string tags that will be appended to the OpenAPI schema.
        type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec
            hook for deserialization.
        type_encoders: A mapping of types to callables that transform them into types supported for serialization.
        handler_class: Route handler class instantiated by the decorator
        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AnyCallable) -> HTTPRouteHandler:
        return handler_class(
            fn=fn,
            after_request=after_request,
            after_response=after_response,
            background=background,
            before_request=before_request,
            cache=cache,
            cache_control=cache_control,
            cache_key_builder=cache_key_builder,
            content_encoding=content_encoding,
            content_media_type=content_media_type,
            dependencies=dependencies,
            deprecated=deprecated,
            description=description,
            dto=dto,
            etag=etag,
            exception_handlers=exception_handlers,
            guards=guards,
            http_method=HttpMethod.DELETE,
            include_in_schema=include_in_schema,
            media_type=media_type,
            middleware=middleware,
            name=name,
            operation_class=operation_class,
            operation_id=operation_id,
            opt=opt,
            path=path,
            raises=raises,
            request_class=request_class,
            response_class=response_class,
            response_cookies=response_cookies,
            response_description=response_description,
            response_headers=response_headers,
            responses=responses,
            return_dto=return_dto,
            security=security,
            signature_namespace=signature_namespace,
            status_code=status_code,
            summary=summary,
            sync_to_thread=sync_to_thread,
            tags=tags,
            type_decoders=type_decoders,
            type_encoders=type_encoders,
            **kwargs,
        )

    return decorator
