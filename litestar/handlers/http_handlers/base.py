from __future__ import annotations

from collections.abc import Awaitable, Iterable, Mapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, AnyStr, Callable, TypedDict, cast

from msgspec.msgpack import decode as _decode_msgpack_plain

from litestar._layers.utils import narrow_response_cookies, narrow_response_headers
from litestar.connection import Request
from litestar.datastructures import CacheControlHeader, ETag, FormMultiDict, Header
from litestar.datastructures.response_header import ResponseHeader
from litestar.enums import HttpMethod, MediaType
from litestar.exceptions import (
    ClientException,
    HTTPException,
    ImproperlyConfiguredException,
    SerializationException,
)
from litestar.handlers.base import BaseRouteHandler
from litestar.handlers.http_handlers._utils import (
    create_data_handler,
    create_generic_asgi_response_handler,
    create_response_handler,
    get_default_status_code,
    is_empty_response_annotation,
    normalize_http_method,
)
from litestar.openapi.spec import Operation
from litestar.response import File, Response
from litestar.response.file import ASGIFileResponse
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_304_NOT_MODIFIED
from litestar.types import (
    AfterRequestHookHandler,
    AfterResponseHookHandler,
    AnyCallable,
    ASGIApp,
    BeforeRequestHookHandler,
    CacheKeyBuilder,
    Dependencies,
    Empty,
    EmptyType,
    ExceptionHandlersMap,
    Guard,
    Method,
    Middleware,
    Receive,
    ResponseCookies,
    ResponseHeaders,
    Scope,
    Send,
    TypeEncodersMap,
)
from litestar.types.builtin_types import NoneType
from litestar.utils import deprecated as litestar_deprecated
from litestar.utils import ensure_async_callable
from litestar.utils.empty import value_or_default
from litestar.utils.predicates import is_async_callable, is_class_and_subclass
from litestar.utils.scope.state import ScopeState
from litestar.utils.warnings import warn_implicit_sync_to_thread, warn_sync_to_thread_with_async_callable

if TYPE_CHECKING:
    from typing import Any

    from litestar import Litestar, Router
    from litestar._kwargs import KwargsModel
    from litestar._kwargs.cleanup import DependencyCleanupGroup
    from litestar.background_tasks import BackgroundTask, BackgroundTasks
    from litestar.config.response_cache import CACHE_FOREVER
    from litestar.datastructures.cookie import Cookie
    from litestar.dto import AbstractDTO
    from litestar.openapi.datastructures import ResponseSpec
    from litestar.openapi.spec import SecurityRequirement
    from litestar.routes import BaseRoute
    from litestar.types.callable_types import (
        AsyncAfterRequestHookHandler,
        AsyncAfterResponseHookHandler,
        AsyncAnyCallable,
        AsyncBeforeRequestHookHandler,
        OperationIDCreator,
    )
    from litestar.types.composite_types import ParametersMap, TypeDecodersSequence
    from litestar.typing import FieldDefinition

__all__ = ("HTTPRouteHandler",)


class ResponseHandlerMap(TypedDict):
    default_handler: Callable[[Any], Awaitable[ASGIApp]] | EmptyType
    response_type_handler: Callable[[Any], Awaitable[ASGIApp]] | EmptyType


class HTTPRouteHandler(BaseRouteHandler):
    __slots__ = (
        "_default_response_handler",
        "_include_in_schema",
        "_kwargs_models",
        "_request_class",
        "_request_max_body_size",
        "_response_class",
        "_response_type_handler",
        "_sync_to_thread",
        "after_request",
        "after_response",
        "background",
        "before_request",
        "cache",
        "cache_control",
        "cache_key_builder",
        "content_encoding",
        "content_media_type",
        "deprecated",
        "description",
        "etag",
        "has_sync_callable",
        "http_methods",
        "media_type",
        "operation_class",
        "operation_id",
        "raises",
        "response_cookies",
        "response_description",
        "response_headers",
        "responses",
        "security",
        "status_code",
        "summary",
        "tags",
    )

    def __init__(
        self,
        path: str | Sequence[str] | None = None,
        *,
        fn: AnyCallable,
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
        http_method: Method | Sequence[Method],
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
        signature_namespace: Mapping[str, Any] | None = None,
        security: Sequence[SecurityRequirement] | None = None,
        summary: str | None = None,
        tags: Sequence[str] | None = None,
        type_decoders: TypeDecodersSequence | None = None,
        type_encoders: TypeEncodersMap | None = None,
        parameters: ParametersMap | None = None,
        **kwargs: Any,
    ) -> None:
        """Route handler for HTTP routes.

        Args:
            path: A path fragment for the route handler function or a sequence of path fragments.
                If not given defaults to ``/``
            fn: The handler function
            after_request: A sync or async function executed before a :class:`Request <.connection.Request>` is passed
                to any route handler. If this function returns a value, the request will not reach the route handler,
                and instead this value will be used.
            after_response: A sync or async function called after the response has been awaited. It receives the
                :class:`Request <.connection.Request>` object and should not return any values.
            background: A :class:`BackgroundTask <.background_tasks.BackgroundTask>` instance or
                :class:`BackgroundTasks <.background_tasks.BackgroundTasks>` to execute after the response is finished.
                Defaults to ``None``.
            before_request: A sync or async function called immediately before calling the route handler. Receives
                the :class:`Request <.connection.Request>` instance and any non-``None`` return value is used for the
                response, bypassing the route handler.
            cache: Enables response caching if configured on the application level. Valid values are ``True`` or a
                number of seconds (e.g. ``120``) to cache the response.
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
                :class:`HttpMethod <.enums.HttpMethod>` or a list of these that correlates to the methods the route
                handler function should handle.
            media_type: A member of the :class:`MediaType <.enums.MediaType>` enum or a string with a valid IANA
                Media-Type.
            middleware: A sequence of :class:`Middleware <.types.Middleware>`.
            name: A string identifying the route handler.
            opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
                wherever you have access to :class:`Request <.connection.Request>` or
                :class:`ASGI Scope <.types.Scope>`.
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
            status_code: An http status code for the response. Defaults to ``200`` for ``GET``, ``PUT`` and ``PATCH``,
                ``201`` for ``POST`` and ``204`` for ``DELETE``. For mixed method requests it will check for ``POST`` and ``DELETE`` first
                then defaults to ``200``.
            sync_to_thread: A boolean dictating whether the handler function will be executed in a worker thread or the
                main event loop. This has an effect only for sync handler functions. See using sync handler functions.
            content_encoding: A string describing the encoding of the content, e.g. ``"base64"``.
            content_media_type: A string designating the media-type of the content, e.g. ``"image/png"``.
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
            type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec hook for deserialization.
            type_encoders: A mapping of types to callables that transform them into types supported for serialization.
            parameters: A mapping of :func:`Parameter <.params.Parameter>` definitions
            **kwargs: Any additional kwarg - will be set in the opt dictionary.
        """
        if not http_method:
            raise ImproperlyConfiguredException("An http_method kwarg is required")

        self.http_methods = normalize_http_method(http_methods=http_method)
        self.status_code = status_code or get_default_status_code(http_methods=self.http_methods)
        self._sync_to_thread = sync_to_thread

        if not is_async_callable(fn):
            if sync_to_thread is None:
                warn_implicit_sync_to_thread(fn, stacklevel=3)
        elif sync_to_thread is not None:
            warn_sync_to_thread_with_async_callable(fn, stacklevel=3)

        has_sync_callable = not is_async_callable(fn)

        if has_sync_callable and sync_to_thread:
            fn = ensure_async_callable(fn)
            has_sync_callable = False
        self.has_sync_callable = has_sync_callable

        super().__init__(
            fn=fn,
            path=path,
            dependencies=dependencies,
            dto=dto,
            exception_handlers=exception_handlers,
            guards=guards,
            middleware=middleware,
            name=name,
            opt=opt,
            return_dto=return_dto,
            signature_namespace=signature_namespace,
            type_decoders=type_decoders,
            type_encoders=type_encoders,
            parameters=parameters,
            **kwargs,
        )

        self.after_request: AsyncAfterRequestHookHandler | None = (
            ensure_async_callable(after_request) if after_request else None  # type: ignore[assignment]
        )
        self.after_response: AsyncAfterResponseHookHandler | None = (
            ensure_async_callable(after_response) if after_response else None
        )
        self.background = background
        self.before_request: AsyncBeforeRequestHookHandler | None = (
            ensure_async_callable(before_request) if before_request else None
        )
        self.cache = cache
        self.cache_control = cache_control
        self.cache_key_builder = cache_key_builder
        self.etag = etag
        self.media_type: MediaType | str = media_type or ""
        self._request_class = request_class
        self._response_class = response_class
        self.response_cookies = frozenset(narrow_response_cookies(response_cookies if response_cookies else ()))
        self.response_headers: frozenset[ResponseHeader] = self._resolve_response_headers(
            response_headers,
            self.etag,
            self.cache_control,
        )
        self._request_max_body_size = request_max_body_size

        # OpenAPI related attributes
        self.content_encoding = content_encoding
        self.content_media_type = content_media_type
        self.deprecated = deprecated
        self.description = description
        self._include_in_schema = include_in_schema
        self.operation_class = operation_class
        self.operation_id = operation_id
        self.raises = raises
        self.response_description = response_description
        self.summary = summary
        self.tags = frozenset(tags) if tags else frozenset()
        self.security = tuple(security) if security else ()
        self.responses = responses
        # memoized attributes, defaulted to Empty
        self._kwargs_models: dict[tuple[str, ...], KwargsModel] = {}
        self._default_response_handler: Callable[[Any], Awaitable[ASGIApp]] | EmptyType = Empty
        self._response_type_handler: Callable[[Any], Awaitable[ASGIApp]] | EmptyType = Empty

    def _get_merge_opts(self, others: tuple[Router, ...]) -> dict[str, Any]:
        merge_opts = super()._get_merge_opts(others)

        # these only exist on the handler, and therefore don't need merging
        merge_opts.update(
            background=self.background,
            http_method=tuple(self.http_methods),
            cache=self.cache,
            media_type=self.media_type,
            status_code=self.status_code,
            # OpenAPI related attributes
            content_encoding=self.content_encoding,
            content_media_type=self.content_media_type,
            deprecated=self.deprecated,
            description=self.description,
            operation_class=self.operation_class,
            operation_id=self.operation_id,
            raises=self.raises,
            response_description=self.response_description,
            responses=self.responses,
            summary=self.summary,
            sync_to_thread=False if self.has_sync_callable else None,
            cache_key_builder=self.cache_key_builder,
        )

        other: HTTPRouteHandler | Router
        for other in (self, *others):  # type: ignore[assignment]
            merge_opts["after_response"] = merge_opts.get("after_response") or other.after_response
            merge_opts["after_request"] = merge_opts.get("after_request") or other.after_request
            merge_opts["before_request"] = merge_opts.get("before_request") or other.before_request
            merge_opts["cache_control"] = merge_opts.get("cache_control") or other.cache_control
            merge_opts["etag"] = merge_opts.get("etag") or other.etag
            merge_opts["response_cookies"] = (*merge_opts.get("response_cookies", ()), *other.response_cookies)
            merge_opts["response_headers"] = (*other.response_headers, *merge_opts.get("response_headers", ()))
            merge_opts["security"] = (*other.security, *merge_opts.get("security", ()))
            merge_opts["tags"] = (*other.tags, *merge_opts.get("tags", ()))

            # these are all properties which return a safe default if the corresponding
            # config value is not set, so we only merge the router configs and determine
            # the final value after that.
            # ideally, a route handler wouldn't be able to take these in as optional,
            # but that would require another 'finalized' route handler, which differs
            # from the config object. this is planned for version 4
            if other is not self:
                merge_opts["request_class"] = merge_opts.get("request_class") or other.request_class
                merge_opts["response_class"] = merge_opts.get("response_class") or other.response_class
                merge_opts["include_in_schema"] = value_or_default(
                    merge_opts.get("include_in_schema", Empty), other.include_in_schema
                )

        merge_opts["request_class"] = self._request_class or merge_opts.get("request_class")
        merge_opts["response_class"] = self._response_class or merge_opts.get("response_class")
        merge_opts["request_max_body_size"] = value_or_default(
            self._request_max_body_size,
            next((o.request_max_body_size for o in others if o.request_max_body_size is not Empty), Empty),
        )
        merge_opts["include_in_schema"] = value_or_default(
            self._include_in_schema, merge_opts.get("include_in_schema", Empty)
        )

        return merge_opts

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".request_class property")
    def resolve_request_class(self) -> type[Request]:
        """Return the closest custom Request class in the owner graph or the default Request class.

        This method is memoized so the computation occurs only once.

        Returns:
            The default :class:`Request <.connection.Request>` class for the route handler.
        """

        return self.request_class

    @property
    def request_class(self) -> type[Request]:
        return self._request_class or Request

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".response_class property")
    def resolve_response_class(self) -> type[Response]:
        """Return the closest custom Response class in the owner graph or the default Response class.

        This method is memoized so the computation occurs only once.

        Returns:
            The default :class:`Response <.response.Response>` class for the route handler.
        """
        return self.response_class

    @property
    def response_class(self) -> type[Response]:
        return self._response_class or Response

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".response_headers attribute")
    def resolve_response_headers(self) -> frozenset[ResponseHeader]:
        return self.response_headers

    @staticmethod
    def _resolve_response_headers(
        response_headers: ResponseHeaders | None,
        *extra_headers: Header | None,
    ) -> frozenset[ResponseHeader]:
        """Return all header parameters in the scope of the handler function.

        Returns:
            A dictionary mapping keys to :class:`ResponseHeader <.datastructures.ResponseHeader>` instances.
        """
        resolved_response_headers: dict[str, ResponseHeader] = (
            {h.name: h for h in narrow_response_headers(response_headers)} if response_headers else {}
        )

        for extra_header in extra_headers:
            if extra_header is None:
                continue
            resolved_response_headers[extra_header.HEADER_NAME] = ResponseHeader(
                name=extra_header.HEADER_NAME,
                value=extra_header.to_header(),
                documentation_only=extra_header.documentation_only,
            )

        return frozenset(resolved_response_headers.values())

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".response_cookies attribute")
    def resolve_response_cookies(self) -> frozenset[Cookie]:
        return self.response_cookies

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".before_request attribute")
    def resolve_before_request(self) -> AsyncAnyCallable | None:
        """Resolve the before_handler handler by starting from the route handler and moving up.

        If a handler is found it is returned, otherwise None is set.
        This method is memoized so the computation occurs only once.

        Returns:
            An optional :class:`before request lifecycle hook handler <.types.BeforeRequestHookHandler>`
        """
        return self.before_request

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".after_response attribute")
    def resolve_after_response(self) -> AsyncAnyCallable | None:
        """Resolve the after_response handler by starting from the route handler and moving up.

        If a handler is found it is returned, otherwise None is set.
        This method is memoized so the computation occurs only once.

        Returns:
            An optional :class:`after response lifecycle hook handler <.types.AfterResponseHookHandler>`
        """
        return self.after_response

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".include_in_schema property")
    def resolve_include_in_schema(self) -> bool:
        """Resolve the 'include_in_schema' property by starting from the route handler and moving up.

        If 'include_in_schema' is found in any of the ownership layers, the last value found is returned.
        If not found in any layer, the default value ``True`` is returned.

        Returns:
            bool: The resolved 'include_in_schema' property.
        """
        return self.include_in_schema

    @property
    def include_in_schema(self) -> bool:
        return self._include_in_schema if self._include_in_schema is not Empty else True

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".security attribute")
    def resolve_security(self) -> tuple[SecurityRequirement, ...]:
        """Resolve the security property by starting from the route handler and moving up.

        Security requirements are additive, so the security requirements of the route handler are the sum of all
        security requirements of the ownership layers.

        Returns:
            list[SecurityRequirement]: The resolved security property.
        """
        return self.security

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".tags attribute")
    def resolve_tags(self) -> frozenset[str]:
        """Resolve the tags property by starting from the route handler and moving up.

        Tags are additive, so the tags of the route handler are the sum of all tags of the ownership layers.
        """
        return self.tags

    @litestar_deprecated("3.0", removal_in="4.0", alternative=".request_max_body_size property")
    def resolve_request_max_body_size(self) -> int | None:
        return self.request_max_body_size

    @property
    def request_max_body_size(self) -> int | None:
        return value_or_default(self._request_max_body_size, None)  # pyright: ignore

    def on_registration(self, route: BaseRoute, app: Litestar) -> None:
        super().on_registration(route=route, app=app)

        if self._request_max_body_size is Empty:
            raise ImproperlyConfiguredException(
                "'request_max_body_size' set to 'Empty' on all layers. To omit a limit, "
                "set 'request_max_body_size=None'"
            )

        self._get_kwargs_model_for_route(route.path_parameters)
        self._default_response_handler, self._response_type_handler = self._create_response_handlers(
            media_type=self.media_type,
            response_class=self.response_class,
            cookies=self.response_cookies,
            headers=self.response_headers,
            type_encoders=self.type_encoders,
            return_type=self.parsed_fn_signature.return_type,
            status_code=self.status_code,
            background=self.background,
            after_request=self.after_request,
        )

    def _get_kwargs_model_for_route(self, path_parameters: Iterable[str]) -> KwargsModel:
        key = tuple(path_parameters)
        if (model := self._kwargs_models.get(key)) is None:
            model = self._kwargs_models[key] = self._create_kwargs_model(path_parameters)
        return model

    def _validate_handler_function(self) -> None:
        """Validate the route handler function once it is set by inspecting its return annotations."""
        super()._validate_handler_function()

        return_type = self.parsed_fn_signature.return_type

        if return_type.annotation is Empty:
            raise ImproperlyConfiguredException(
                f"Missing return type annotation for route handler function {self!r}. "
                "If your function doesn't return a value, annotate it as returning 'None'."
            )

        if (
            self.status_code < 200 or self.status_code in {HTTP_204_NO_CONTENT, HTTP_304_NOT_MODIFIED}
        ) and not is_empty_response_annotation(return_type):
            raise ImproperlyConfiguredException(
                "A status code 204, 304 or in the range below 200 does not support a response body. "
                "If the function should return a value, change the route handler status code to an appropriate value.",
            )

        if not self.media_type:
            if return_type.is_subclass_of((str, bytes)) or return_type.annotation is AnyStr:
                self.media_type = MediaType.TEXT
            elif not return_type.is_subclass_of(Response):
                self.media_type = MediaType.JSON

        if "socket" in self.parsed_fn_signature.parameters:
            raise ImproperlyConfiguredException("The 'socket' kwarg is not supported with http handlers")

        if "data" in self.parsed_fn_signature.parameters and "GET" in self.http_methods:
            raise ImproperlyConfiguredException("'data' kwarg is unsupported for 'GET' request handlers")

        if self.http_methods == {HttpMethod.HEAD} and not self.parsed_fn_signature.return_type.is_subclass_of(
            (NoneType, File, ASGIFileResponse)
        ):
            field_definition = self.parsed_fn_signature.return_type
            if not (
                is_empty_response_annotation(field_definition)
                or is_class_and_subclass(field_definition.annotation, File)
                or is_class_and_subclass(field_definition.annotation, ASGIFileResponse)
            ):
                raise ImproperlyConfiguredException(
                    f"{self}: Handlers for 'HEAD' requests must not return a value. Either return 'None' or a response type without a body."
                )

        if (body_param := self.parsed_fn_signature.parameters.get("body")) and not body_param.is_subclass_of(bytes):
            raise ImproperlyConfiguredException(
                f"Invalid type annotation for 'body' parameter in route handler {self}. 'body' will always receive the "
                f"raw request body as bytes but was annotated with '{body_param.raw!r}'. If you want to receive "
                "processed request data, use the 'data' parameter."
            )

    @staticmethod
    def _create_response_handlers(
        *,
        media_type: MediaType | str,
        response_class: type[Response],
        headers: frozenset[ResponseHeader],
        cookies: frozenset[Cookie],
        type_encoders: TypeEncodersMap,
        return_type: FieldDefinition,
        status_code: int,
        background: BackgroundTask | BackgroundTasks | None,
        after_request: AfterRequestHookHandler | None,
    ) -> tuple[Callable[..., Awaitable[ASGIApp]], Callable[..., Awaitable[ASGIApp]]]:
        media_type = media_type.value if isinstance(media_type, Enum) else media_type
        return_annotation = return_type.annotation

        response_type_handler = create_response_handler(
            after_request=after_request,
            background=background,
            cookies=cookies,
            headers=headers,
            media_type=media_type,
            status_code=status_code,
            type_encoders=type_encoders,
        )

        if is_async_callable(return_annotation) or return_annotation is ASGIApp:
            default_handler = create_generic_asgi_response_handler(after_request=after_request)
        else:
            default_handler = create_data_handler(
                after_request=after_request,
                background=background,
                cookies=cookies,
                headers=headers,
                media_type=media_type,
                response_class=response_class,
                status_code=status_code,
                type_encoders=type_encoders,
            )

        return default_handler, response_type_handler

    async def handle(self, connection: Request[Any, Any, Any]) -> None:
        """ASGI app that creates a :class:`~.connection.Request` from the passed in args, determines which handler function to call and then
            handles the call.

        .. versionadded: 3.0

        Args:
                connection: The request

        Returns:
                None
        """

        if self.guards:
            await self.authorize_connection(connection=connection)

        try:
            response = await self._get_response_for_request(request=connection)

            await response(connection.scope, connection.receive, connection.send)

            if after_response_handler := self.after_response:
                await after_response_handler(connection)
        finally:
            if (form_data := ScopeState.from_scope(connection.scope).form) is not Empty:
                await FormMultiDict.from_form_data(form_data).close()

    async def _get_response_for_request(
        self,
        request: Request[Any, Any, Any],
    ) -> ASGIApp:
        """Return a response for the request.

        If caching is enabled and a response exist in the cache, the cached response will be returned.
        If caching is enabled and a response does not exist in the cache, the newly created
        response will be cached.

        Args:
            request: The Request instance

        Returns:
            An instance of Response or a compatible ASGIApp or a subclass of it
        """
        if self.cache and (cached_response := await self._get_cached_response(request=request)):
            return cached_response

        response_data: Any = None
        cleanup_group: DependencyCleanupGroup | None = None

        if before_request_handler := self.before_request:
            response_data = await before_request_handler(request)

        if not response_data:
            response_data, cleanup_group = await self._get_response_data(request=request)

        response: ASGIApp = await self.to_response(data=response_data, request=request)

        if cleanup_group:
            await cleanup_group.cleanup()

        return response

    async def _get_response_data(self, request: Request) -> tuple[Any, DependencyCleanupGroup | None]:
        """Determine what kwargs are required for the given route handler's ``fn`` and calls it."""
        parsed_kwargs: dict[str, Any] = {}
        cleanup_group: DependencyCleanupGroup | None = None
        kwargs_models_model = self._get_kwargs_model_for_route(request.scope["path_params"].keys())

        if kwargs_models_model.has_kwargs and self.signature_model:
            try:
                kwargs = await kwargs_models_model.to_kwargs(connection=request)
            except SerializationException as e:
                raise ClientException(str(e)) from e

            if "data" in kwargs and kwargs["data"] is Empty:
                del kwargs["data"]

            if kwargs_models_model.dependency_batches:
                cleanup_group = await kwargs_models_model.resolve_dependencies(request, kwargs)

            parsed_kwargs = self.signature_model.parse_values_from_connection_kwargs(
                connection=request,
                kwargs=kwargs,
            )

        if cleanup_group:
            async with cleanup_group:
                data = self.fn(**parsed_kwargs) if self.has_sync_callable else await self.fn(**parsed_kwargs)
        elif self.has_sync_callable:
            data = self.fn(**parsed_kwargs)
        else:
            data = await self.fn(**parsed_kwargs)

        return data, cleanup_group

    async def _get_cached_response(self, request: Request) -> ASGIApp | None:
        """Retrieve and un-pickle the cached response, if existing.

        Args:
            request: The :class:`Request <litestar.connection.Request>` instance

        Returns:
            A cached response instance, if existing.
        """

        cache_config = request.app.response_cache_config
        cache_key = (self.cache_key_builder or cache_config.key_builder)(request)
        store = cache_config.get_store_from_app(request.app)

        if not (cached_response_data := await store.get(key=cache_key)):
            return None

        # we use the regular msgspec.msgpack.decode here since we don't need any of
        # the added decoders
        messages = _decode_msgpack_plain(cached_response_data)

        async def cached_response(scope: Scope, receive: Receive, send: Send) -> None:
            ScopeState.from_scope(scope).is_cached = True
            for message in messages:
                await send(message)

        return cached_response

    async def to_response(self, data: Any, request: Request) -> ASGIApp:
        """Return a :class:`Response <.response.Response>` from the handler by resolving and calling it.

        Args:
            data: Either an instance of a :class:`Response <.response.Response>`,
                a Response instance or an arbitrary value.
            request: A :class:`Request <.connection.Request>` instance

        Returns:
            A Response instance
        """
        if return_dto_type := self.return_dto:
            data = return_dto_type(request).data_to_encodable_type(data)

        handler = cast(
            Callable[..., Awaitable[ASGIApp]],
            self._response_type_handler if isinstance(data, Response) else self._default_response_handler,
        )

        return await handler(data=data, request=request)
