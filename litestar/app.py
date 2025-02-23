from __future__ import annotations

import collections
import inspect
import itertools
import logging
import os
import warnings
from collections import defaultdict
from contextlib import (
    AbstractAsyncContextManager,
    AsyncExitStack,
    asynccontextmanager,
    suppress,
)
from datetime import date, datetime, time, timedelta
from functools import partial
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, TypedDict, cast
from uuid import UUID

from litestar._asgi import ASGIRouter
from litestar._asgi.utils import get_route_handlers, wrap_in_exception_handler
from litestar._openapi.plugin import OpenAPIPlugin
from litestar._openapi.schema_generation import openapi_schema_plugins
from litestar.config.allowed_hosts import AllowedHostsConfig
from litestar.config.app import AppConfig, ExperimentalFeatures
from litestar.config.response_cache import ResponseCacheConfig
from litestar.connection import Request, WebSocket
from litestar.datastructures.state import State
from litestar.events.emitter import BaseEventEmitterBackend, SimpleEventEmitter
from litestar.exceptions import (
    ImproperlyConfiguredException,
    LitestarWarning,
    MissingDependencyException,
    NoRouteMatchFoundException,
)
from litestar.handlers import ASGIRouteHandler, BaseRouteHandler, HTTPRouteHandler, WebsocketRouteHandler
from litestar.handlers.http_handlers._options import create_options_handler
from litestar.logging.config import LoggingConfig, get_logger_placeholder
from litestar.middleware._internal.cors import CORSMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.plugins import (
    CLIPluginProtocol,
    InitPluginProtocol,
    OpenAPISchemaPluginProtocol,
    PluginProtocol,
    PluginRegistry,
    SerializationPluginProtocol,
)
from litestar.plugins.base import CLIPlugin
from litestar.router import Router
from litestar.routes import ASGIRoute, HTTPRoute, WebSocketRoute
from litestar.stores.registry import StoreRegistry
from litestar.types import Empty, TypeDecodersSequence
from litestar.types.internal_types import PathParameterDefinition, RouteHandlerMapItem, TemplateConfigType
from litestar.utils import deprecated, ensure_async_callable, join_paths, unique
from litestar.utils.dataclass import extract_dataclass_items
from litestar.utils.predicates import is_async_callable, is_class_and_subclass
from litestar.utils.warnings import warn_pdb_on_exception

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator, Iterable, Mapping, Sequence

    from typing_extensions import Self

    from litestar.config.compression import CompressionConfig
    from litestar.config.cors import CORSConfig
    from litestar.config.csrf import CSRFConfig
    from litestar.contrib.opentelemetry import OpenTelemetryPlugin
    from litestar.datastructures import CacheControlHeader, ETag
    from litestar.dto import AbstractDTO
    from litestar.events.listener import EventListener
    from litestar.logging.config import BaseLoggingConfig
    from litestar.openapi.spec import SecurityRequirement
    from litestar.openapi.spec.open_api import OpenAPI
    from litestar.response import Response
    from litestar.stores.base import Store
    from litestar.types import (
        AfterExceptionHookHandler,
        AfterRequestHookHandler,
        AfterResponseHookHandler,
        ASGIApp,
        BeforeMessageSendHookHandler,
        BeforeRequestHookHandler,
        ControllerRouterHandler,
        Dependencies,
        EmptyType,
        ExceptionHandlersMap,
        GetLogger,
        Guard,
        LifeSpanReceive,
        LifeSpanScope,
        LifeSpanSend,
        Logger,
        Message,
        Middleware,
        OnAppInitHandler,
        ParametersMap,
        Receive,
        ResponseCookies,
        ResponseHeaders,
        RouteHandlerType,
        Scope,
        Send,
        TypeEncodersMap,
    )
    from litestar.types.callable_types import LifespanHook


__all__ = ("DEFAULT_OPENAPI_CONFIG", "HandlerIndex", "Litestar")

DEFAULT_OPENAPI_CONFIG = OpenAPIConfig(title="Litestar API", version="1.0.0")
"""The default OpenAPI config used if not configuration is explicitly passed to the
:class:`Litestar <.app.Litestar>` instance constructor.
"""


class HandlerIndex(TypedDict):
    """Map route handler names to a mapping of paths + route handler.

    It's returned from the 'get_handler_index_by_name' utility method.
    """

    paths: list[str]
    """Full route paths to the route handler."""
    handler: RouteHandlerType
    """Route handler instance."""
    identifier: str
    """Unique identifier of the handler.

    Either equal to ``__name__`` attribute or ``__str__`` value of the handler.
    """


class Litestar(Router):
    """The Litestar application.

    ``Litestar`` is the root level of the app - it has the base path of ``/`` and all root level Controllers, Routers
    and Route Handlers should be registered on it.
    """

    __slots__ = (
        "_debug",
        "_lifespan_managers",
        "_openapi_schema",
        "_server_lifespan_managers",
        "after_exception",
        "allowed_hosts",
        "asgi_handler",
        "asgi_router",
        "before_send",
        "compression_config",
        "cors_config",
        "csrf_config",
        "event_emitter",
        "experimental_features",
        "get_logger",
        "logger",
        "logging_config",
        "multipart_form_part_limit",
        "on_shutdown",
        "on_startup",
        "openapi_config",
        "pdb_on_exception",
        "plugins",
        "response_cache_config",
        "route_handler_method_map",
        "route_map",
        "routes",
        "state",
        "stores",
        "template_engine",
    )

    def __init__(
        self,
        route_handlers: Sequence[ControllerRouterHandler] | None = None,
        *,
        after_exception: Sequence[AfterExceptionHookHandler] | None = None,
        after_request: AfterRequestHookHandler | None = None,
        after_response: AfterResponseHookHandler | None = None,
        allowed_hosts: Sequence[str] | AllowedHostsConfig | None = None,
        before_request: BeforeRequestHookHandler | None = None,
        before_send: Sequence[BeforeMessageSendHookHandler] | None = None,
        cache_control: CacheControlHeader | None = None,
        compression_config: CompressionConfig | None = None,
        cors_config: CORSConfig | None = None,
        csrf_config: CSRFConfig | None = None,
        dto: type[AbstractDTO] | None | EmptyType = Empty,
        debug: bool | None = None,
        dependencies: Dependencies | None = None,
        etag: ETag | None = None,
        event_emitter_backend: type[BaseEventEmitterBackend] = SimpleEventEmitter,
        exception_handlers: ExceptionHandlersMap | None = None,
        guards: Sequence[Guard] | None = None,
        include_in_schema: bool | EmptyType = Empty,
        listeners: Sequence[EventListener] | None = None,
        logging_config: BaseLoggingConfig | EmptyType | None = Empty,
        middleware: Sequence[Middleware] | None = None,
        multipart_form_part_limit: int = 1000,
        on_app_init: Sequence[OnAppInitHandler] | None = None,
        on_shutdown: Sequence[LifespanHook] | None = None,
        on_startup: Sequence[LifespanHook] | None = None,
        openapi_config: OpenAPIConfig | None = DEFAULT_OPENAPI_CONFIG,
        opt: Mapping[str, Any] | None = None,
        parameters: ParametersMap | None = None,
        path: str | None = None,
        plugins: Sequence[PluginProtocol] | None = None,
        request_class: type[Request] | None = None,
        request_max_body_size: int | None = 10_000_000,
        response_cache_config: ResponseCacheConfig | None = None,
        response_class: type[Response] | None = None,
        response_cookies: ResponseCookies | None = None,
        response_headers: ResponseHeaders | None = None,
        return_dto: type[AbstractDTO] | None | EmptyType = Empty,
        security: Sequence[SecurityRequirement] | None = None,
        signature_namespace: Mapping[str, Any] | None = None,
        signature_types: Sequence[Any] | None = None,
        state: State | None = None,
        stores: StoreRegistry | dict[str, Store] | None = None,
        tags: Sequence[str] | None = None,
        template_config: TemplateConfigType | None = None,
        type_decoders: TypeDecodersSequence | None = None,
        type_encoders: TypeEncodersMap | None = None,
        websocket_class: type[WebSocket] | None = None,
        lifespan: Sequence[Callable[[Litestar], AbstractAsyncContextManager] | AbstractAsyncContextManager]
        | None = None,
        pdb_on_exception: bool | None = None,
        experimental_features: Iterable[ExperimentalFeatures] | None = None,
    ) -> None:
        """Initialize a ``Litestar`` application.

        Args:
            after_exception: A sequence of :class:`exception hook handlers <.types.AfterExceptionHookHandler>`. This
                hook is called after an exception occurs. In difference to exception handlers, it is not meant to
                return a response - only to process the exception (e.g. log it, send it to Sentry etc.).
            after_request: A sync or async function executed after the route handler function returned and the response
                object has been resolved. Receives the response object.
            after_response: A sync or async function called after the response has been awaited. It receives the
                :class:`Request <.connection.Request>` object and should not return any values.
            allowed_hosts: A sequence of allowed hosts, or an
                :class:`AllowedHostsConfig <.config.allowed_hosts.AllowedHostsConfig>` instance. Enables the builtin
                allowed hosts middleware.
            before_request: A sync or async function called immediately before calling the route handler. Receives the
                :class:`Request <.connection.Request>` instance and any non-``None`` return value is used for the
                response, bypassing the route handler.
            before_send: A sequence of :class:`before send hook handlers <.types.BeforeMessageSendHookHandler>`. Called
                when the ASGI send function is called.
            cache_control: A ``cache-control`` header of type
                :class:`CacheControlHeader <litestar.datastructures.CacheControlHeader>` to add to route handlers of
                this app. Can be overridden by route handlers.
            compression_config: Configures compression behaviour of the application, this enabled a builtin or user
                defined Compression middleware.
            cors_config: If set, configures CORS handling for the application.
            csrf_config: If set, configures :class:`CSRFMiddleware <.middleware.csrf.CSRFMiddleware>`.
            debug: If ``True``, app errors rendered as HTML with a stack trace.
            dependencies: A string keyed mapping of dependency :class:`Providers <.di.Provide>`.
            dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
                validation of request data.
            etag: An ``etag`` header of type :class:`ETag <.datastructures.ETag>` to add to route handlers of this app.
                Can be overridden by route handlers.
            event_emitter_backend: A subclass of
                :class:`BaseEventEmitterBackend <.events.emitter.BaseEventEmitterBackend>`.
            exception_handlers: A mapping of status codes and/or exception types to handler functions.
            guards: A sequence of :class:`Guard <.types.Guard>` callables.
            include_in_schema: A boolean flag dictating whether  the route handler should be documented in the OpenAPI schema.
            lifespan: A list of callables returning async context managers, wrapping the lifespan of the ASGI application
            listeners: A sequence of :class:`EventListener <.events.listener.EventListener>`.
            logging_config: A subclass of :class:`BaseLoggingConfig <.logging.config.BaseLoggingConfig>`.
            middleware: A sequence of :class:`Middleware <.types.Middleware>`.
            multipart_form_part_limit: The maximal number of allowed parts in a multipart/formdata request. This limit
                is intended to protect from DoS attacks.
            on_app_init: A sequence of :class:`OnAppInitHandler <.types.OnAppInitHandler>` instances. Handlers receive
                an instance of :class:`AppConfig <.config.app.AppConfig>` that will have been initially populated with
                the parameters passed to :class:`Litestar <litestar.app.Litestar>`, and must return an instance of same.
                If more than one handler is registered they are called in the order they are provided.
            on_shutdown: A sequence of :class:`LifespanHook <.types.LifespanHook>` called during application
                shutdown.
            on_startup: A sequence of :class:`LifespanHook <litestar.types.LifespanHook>` called during
                application startup.
            openapi_config: Defaults to :attr:`DEFAULT_OPENAPI_CONFIG`
            opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
                wherever you have access to :class:`Request <litestar.connection.request.Request>` or
                :class:`ASGI Scope <.types.Scope>`.
            parameters: A mapping of :class:`Parameter <.params.Parameter>` definitions available to all application
                paths.
            path: A path fragment that is prefixed to all route handlers, controllers and routers associated
                with the application instance.

                .. versionadded:: 2.8.0
            pdb_on_exception: Drop into the PDB when an exception occurs.
            plugins: Sequence of plugins.
            request_class: An optional subclass of :class:`Request <.connection.Request>` to use for http connections.
            request_max_body_size: Maximum allowed size of the request body in bytes. If this size is exceeded, a
                '413 - Request Entity Too Large' error response is returned.
            response_class: A custom subclass of :class:`Response <.response.Response>` to be used as the app's default
                response.
            response_cookies: A sequence of :class:`Cookie <.datastructures.Cookie>`.
            response_headers: A string keyed mapping of :class:`ResponseHeader <.datastructures.ResponseHeader>`
            response_cache_config: Configures caching behavior of the application.
            return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
                outbound response data.
            route_handlers: A sequence of route handlers, which can include instances of
                :class:`Router <.router.Router>`, subclasses of :class:`Controller <.controller.Controller>` or any
                callable decorated by the route handler decorators.
            security: A sequence of dicts that will be added to the schema of all route handlers in the application.
                See
                :data:`SecurityRequirement <.openapi.spec.SecurityRequirement>` for details.
            signature_namespace: A mapping of names to types for use in forward reference resolution during signature modeling.
            signature_types: A sequence of types for use in forward reference resolution during signature modeling.
                These types will be added to the signature namespace using their ``__name__`` attribute.
            state: An optional :class:`State <.datastructures.State>` for application state.
            stores: Central registry of :class:`Store <.stores.base.Store>` that will be available throughout the
                application. If this is a dictionary to it will be passed to a
                :class:`StoreRegistry <.stores.registry.StoreRegistry>`. If it is a
                :class:`StoreRegistry <.stores.registry.StoreRegistry>`, this instance will be used directly.
            tags: A sequence of string tags that will be appended to the schema of all route handlers under the
                application.
            template_config: An instance of :class:`TemplateConfig <.template.TemplateConfig>`
            type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec
                hook for deserialization.
            type_encoders: A mapping of types to callables that transform them into types supported for serialization.
            websocket_class: An optional subclass of :class:`WebSocket <.connection.WebSocket>` to use for websocket
                connections.
            experimental_features: An iterable of experimental features to enable
        """

        if logging_config is Empty:
            logging_config = LoggingConfig()

        if debug is None:
            debug = os.getenv("LITESTAR_DEBUG", "0") == "1"

        if pdb_on_exception is None:
            pdb_on_exception = os.getenv("LITESTAR_PDB", "0") == "1"

        config = AppConfig(
            after_exception=list(after_exception or []),
            after_request=after_request,
            after_response=after_response,
            allowed_hosts=allowed_hosts if isinstance(allowed_hosts, AllowedHostsConfig) else list(allowed_hosts or []),
            before_request=before_request,
            before_send=list(before_send or []),
            cache_control=cache_control,
            compression_config=compression_config,
            cors_config=cors_config,
            csrf_config=csrf_config,
            debug=debug,
            dependencies=dict(dependencies or {}),
            dto=dto,
            etag=etag,
            event_emitter_backend=event_emitter_backend,
            exception_handlers=exception_handlers or {},
            guards=list(guards or []),
            include_in_schema=include_in_schema,
            lifespan=list(lifespan or []),
            listeners=list(listeners or []),
            logging_config=logging_config,
            middleware=list(middleware or []),
            multipart_form_part_limit=multipart_form_part_limit,
            on_shutdown=list(on_shutdown or []),
            on_startup=list(on_startup or []),
            openapi_config=openapi_config,
            opt=dict(opt or {}),
            path=path or "",
            parameters=parameters or {},
            pdb_on_exception=pdb_on_exception,
            plugins=self._get_default_plugins(list(plugins or [])),
            request_class=request_class,
            request_max_body_size=request_max_body_size,
            response_cache_config=response_cache_config or ResponseCacheConfig(),
            response_class=response_class,
            response_cookies=response_cookies or [],
            response_headers=response_headers or [],
            return_dto=return_dto,
            route_handlers=list(route_handlers) if route_handlers is not None else [],
            security=list(security or []),
            signature_namespace=dict(signature_namespace or {}),
            signature_types=list(signature_types or []),
            state=state or State(),
            stores=stores,
            tags=list(tags or []),
            template_config=template_config,
            type_encoders=type_encoders,
            type_decoders=type_decoders,
            websocket_class=websocket_class,
            experimental_features=list(experimental_features or []),
        )

        config.plugins.extend([OpenAPIPlugin(self), *openapi_schema_plugins])

        for handler in chain(
            on_app_init or [],
            (p.on_app_init for p in config.plugins if isinstance(p, InitPluginProtocol)),
            [self._patch_opentelemetry_middleware],
        ):
            config = handler(config)  # pyright: ignore

        self.plugins = PluginRegistry(config.plugins)

        self._openapi_schema: OpenAPI | None = None
        self._debug: bool = True
        self.stores: StoreRegistry = (
            config.stores if isinstance(config.stores, StoreRegistry) else StoreRegistry(config.stores)
        )
        self._lifespan_managers = config.lifespan
        for store in self.stores._stores.values():
            self._lifespan_managers.append(store)
        self._server_lifespan_managers = [p.server_lifespan for p in config.plugins or [] if isinstance(p, CLIPlugin)]
        self.experimental_features = frozenset(config.experimental_features or [])
        if ExperimentalFeatures.DTO_CODEGEN in self.experimental_features:
            warnings.warn(
                "Use of redundant experimental feature flag DTO_CODEGEN. "
                "DTO codegen backend is enabled by default since Litestar 2.8. The "
                "DTO_CODEGEN feature flag can be safely removed from the configuration "
                "and will be removed in version 3.0.",
                category=LitestarWarning,
                stacklevel=2,
            )

        self.get_logger: GetLogger = get_logger_placeholder
        self.logger: Logger | None = None

        self.after_exception = [ensure_async_callable(h) for h in config.after_exception]
        self.allowed_hosts = cast("AllowedHostsConfig | None", config.allowed_hosts)
        self.before_send = [ensure_async_callable(h) for h in config.before_send]
        self.compression_config = config.compression_config
        self.cors_config = config.cors_config
        self.csrf_config = config.csrf_config
        self.event_emitter = config.event_emitter_backend(listeners=config.listeners)
        self.logging_config = config.logging_config
        self.multipart_form_part_limit = config.multipart_form_part_limit
        self.on_shutdown = config.on_shutdown
        self.on_startup = config.on_startup
        self.openapi_config = config.openapi_config
        self.request_class: type[Request] = config.request_class or Request
        self.response_cache_config = config.response_cache_config
        self.state = config.state
        self.template_engine = config.template_config.engine_instance if config.template_config else None
        self.websocket_class: type[WebSocket] = config.websocket_class or WebSocket
        self.debug = config.debug
        self.pdb_on_exception: bool = config.pdb_on_exception
        self.include_in_schema = include_in_schema

        if self.pdb_on_exception:
            warn_pdb_on_exception()

        try:
            from starlette.exceptions import HTTPException as StarletteHTTPException

            from litestar.middleware._internal.exceptions.middleware import _starlette_exception_handler

            config.exception_handlers.setdefault(StarletteHTTPException, _starlette_exception_handler)
        except ImportError:
            pass
        super().__init__(
            after_request=config.after_request,
            after_response=config.after_response,
            before_request=config.before_request,
            cache_control=config.cache_control,
            dependencies=config.dependencies,
            dto=config.dto,
            etag=config.etag,
            exception_handlers=config.exception_handlers,
            guards=config.guards,
            middleware=config.middleware,
            opt=config.opt,
            parameters=config.parameters,
            path=config.path,
            request_class=self.request_class,
            request_max_body_size=request_max_body_size,
            response_class=config.response_class,
            response_cookies=config.response_cookies,
            response_headers=config.response_headers,
            return_dto=config.return_dto,
            route_handlers=config.route_handlers,
            security=config.security,
            signature_namespace=config.signature_namespace,
            signature_types=config.signature_types,
            tags=config.tags,
            type_encoders=config.type_encoders,
            type_decoders=config.type_decoders,
            include_in_schema=config.include_in_schema,
            websocket_class=self.websocket_class,
        )

        self.asgi_router = ASGIRouter(app=self)

        self.routes: list[HTTPRoute | ASGIRoute | WebSocketRoute] = self._build_routes(
            self._reduce_handlers(self.route_handlers)
        )
        self.route_handler_method_map = self._create_route_handler_method_map(self.routes)

        # we have merged everything registered initially, so let's ensure we don't keep
        # unnecessary references to temporary objects around and let them be gc'ed
        self.route_handlers = ()

        self.asgi_router.construct_routing_trie()

        if self.logging_config:
            self.get_logger = self.logging_config.configure()
            self.logger = self.get_logger("litestar")

        self.asgi_handler = self._create_asgi_handler()

    @staticmethod
    def _patch_opentelemetry_middleware(config: AppConfig) -> AppConfig:
        # workaround to support otel middleware priority. Should be replaced by regular
        # middleware priorities once available
        try:
            from litestar.contrib.opentelemetry import OpenTelemetryPlugin

            if not any(isinstance(p, OpenTelemetryPlugin) for p in config.plugins):
                config.middleware, otel_middleware = OpenTelemetryPlugin._pop_otel_middleware(config.middleware)
                if otel_middleware:
                    otel_plugin = OpenTelemetryPlugin()
                    otel_plugin._middleware = otel_middleware
                    config.plugins = [*config.plugins, otel_plugin]
        except ImportError:
            pass
        return config

    @property
    @deprecated(version="2.0", alternative="Litestar.plugins.cli", kind="property")
    def cli_plugins(self) -> list[CLIPluginProtocol]:
        return list(self.plugins.cli)

    @property
    @deprecated(version="2.0", alternative="Litestar.plugins.openapi", kind="property")
    def openapi_schema_plugins(self) -> list[OpenAPISchemaPluginProtocol]:
        return list(self.plugins.openapi)

    @property
    @deprecated(version="2.0", alternative="Litestar.plugins.serialization", kind="property")
    def serialization_plugins(self) -> list[SerializationPluginProtocol]:
        return list(self.plugins.serialization)

    @staticmethod
    def _get_default_plugins(plugins: list[PluginProtocol]) -> list[PluginProtocol]:
        from litestar.plugins.core import MsgspecDIPlugin

        plugins.append(MsgspecDIPlugin())

        with suppress(MissingDependencyException):
            from litestar.plugins.pydantic import (
                PydanticDIPlugin,
                PydanticInitPlugin,
                PydanticPlugin,
                PydanticSchemaPlugin,
            )

            pydantic_plugin_found = any(isinstance(plugin, PydanticPlugin) for plugin in plugins)
            pydantic_init_plugin_found = any(isinstance(plugin, PydanticInitPlugin) for plugin in plugins)
            pydantic_schema_plugin_found = any(isinstance(plugin, PydanticSchemaPlugin) for plugin in plugins)
            pydantic_serialization_plugin_found = any(isinstance(plugin, PydanticDIPlugin) for plugin in plugins)
            if not pydantic_plugin_found and not pydantic_init_plugin_found and not pydantic_schema_plugin_found:
                plugins.append(PydanticPlugin())
            elif not pydantic_plugin_found and pydantic_init_plugin_found and not pydantic_schema_plugin_found:
                plugins.append(PydanticSchemaPlugin())
            elif not pydantic_plugin_found and not pydantic_init_plugin_found:
                plugins.append(PydanticInitPlugin())
            if not pydantic_plugin_found and not pydantic_serialization_plugin_found:
                plugins.append(PydanticDIPlugin())
        with suppress(MissingDependencyException):
            from litestar.plugins.attrs import AttrsSchemaPlugin

            pre_configured = any(isinstance(plugin, AttrsSchemaPlugin) for plugin in plugins)
            if not pre_configured:
                plugins.append(AttrsSchemaPlugin())
        return plugins

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        """Sets the debug logging level for the application.

        When possible, it calls the `self.logging_config.set_level` method.  This allows for implementation specific code and APIs to be called.
        """
        if self.logger and self.logging_config:
            self.logging_config.set_level(self.logger, logging.DEBUG if value else logging.INFO)
        elif self.logger and hasattr(self.logger, "setLevel"):  # pragma: no cover
            self.logger.setLevel(logging.DEBUG if value else logging.INFO)  # pragma: no cover
        if isinstance(self.logging_config, LoggingConfig):
            self.logging_config.loggers["litestar"]["level"] = "DEBUG" if value else "INFO"
        self._debug = value

    async def __call__(
        self,
        scope: Scope | LifeSpanScope,
        receive: Receive | LifeSpanReceive,
        send: Send | LifeSpanSend,
    ) -> None:
        """Application entry point.

        Lifespan events (startup / shutdown) are sent to the lifespan handler, otherwise the ASGI handler is used

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None
        """
        if scope["type"] == "lifespan":
            await self.asgi_router.lifespan(receive=receive, send=send)  # type: ignore[arg-type]
            return

        scope["app"] = scope["litestar_app"] = self
        scope.setdefault("state", {})
        await self.asgi_handler(scope, receive, self._wrap_send(send=send, scope=scope))  # type: ignore[arg-type]

    @classmethod
    def from_scope(cls, scope: Scope) -> Litestar:
        """Retrieve the Litestar application from the current ASGI scope"""
        return scope["litestar_app"]

    async def _call_lifespan_hook(self, hook: LifespanHook) -> None:
        ret = hook(self) if inspect.signature(hook).parameters else hook()  # type: ignore[call-arg]

        if is_async_callable(hook):  # pyright: ignore[reportGeneralTypeIssues]
            await ret

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None, None]:
        """Context manager handling the ASGI lifespan.

        It will be entered when the ``lifespan`` message has been received from the
        server, and exit after the ``asgi.shutdown`` message. During this period, it is
        responsible for calling the ``on_startup``, ``on_shutdown`` hooks, as well as
        custom lifespan managers.
        """
        async with AsyncExitStack() as exit_stack:
            for hook in self.on_shutdown[::-1]:
                exit_stack.push_async_callback(partial(self._call_lifespan_hook, hook))

            await exit_stack.enter_async_context(self.event_emitter)

            for manager in self._lifespan_managers:
                if not isinstance(manager, AbstractAsyncContextManager):
                    manager = manager(self)
                await exit_stack.enter_async_context(manager)

            for hook in self.on_startup:
                await self._call_lifespan_hook(hook)

            yield

    @property
    def openapi_schema(self) -> OpenAPI:
        """Access  the OpenAPI schema of the application.

        Returns:
            The :class:`OpenAPI`
            <pydantic_openapi_schema.open_api.OpenAPI> instance of the
            application.

        Raises:
            ImproperlyConfiguredException: If the application ``openapi_config`` attribute is ``None``.
        """
        return self.plugins.get(OpenAPIPlugin).provide_openapi()

    @classmethod
    def from_config(cls, config: AppConfig) -> Self:
        """Initialize a ``Litestar`` application from a configuration instance.

        Args:
            config: An instance of :class:`AppConfig` <.config.AppConfig>

        Returns:
            An instance of ``Litestar`` application.
        """
        return cls(**dict(extract_dataclass_items(config)))

    @staticmethod
    def _create_route_handler_method_map(
        routes: Sequence[HTTPRoute | ASGIRoute | WebSocketRoute],
    ) -> dict[str, RouteHandlerMapItem]:
        """Map route paths to :class:`~litestar.types.internal_types.RouteHandlerMapItem`

        Returns:
             A dictionary mapping paths to route handlers
        """
        route_map: defaultdict[str, RouteHandlerMapItem] = defaultdict(dict)
        for route in routes:
            if isinstance(route, HTTPRoute):
                route_map[route.path] = route.route_handler_map  # type: ignore[assignment]
            else:
                route_map[route.path]["websocket" if isinstance(route, WebSocketRoute) else "asgi"] = (
                    route.route_handler
                )

        return route_map

    def _build_routes(self, route_handlers: Iterable[BaseRouteHandler]) -> list[HTTPRoute | ASGIRoute | WebSocketRoute]:
        """Create routes for all the handlers"""
        routes: list[HTTPRoute | ASGIRoute | WebSocketRoute] = []

        # since http routes can have multiple handlers (the case when one path handles
        # multiple methods - we do the last mile of the routing outside the trie and on
        # the route itself), we first group them by path and then create one route for
        # each path
        http_path_groups: dict[str, list[HTTPRouteHandler]] = collections.defaultdict(list)

        for handler in route_handlers:
            if isinstance(handler, HTTPRouteHandler):
                for path in handler.paths:
                    http_path_groups[path].append(handler)
            elif isinstance(handler, WebsocketRouteHandler):
                for path in handler.paths:
                    routes.append(WebSocketRoute(path=path, route_handler=handler))
            elif isinstance(handler, ASGIRouteHandler):
                for path in handler.paths:
                    routes.append(ASGIRoute(path=path, route_handler=handler))

        for path, http_handlers in http_path_groups.items():
            routes.append(
                HTTPRoute(path=path, route_handlers=_maybe_add_options_handler(path, http_handlers, root=self))
            )

        for finalized_route in routes:
            route_handlers = get_route_handlers(finalized_route)

            for route_handler in route_handlers:
                route_handler.on_registration(route=finalized_route, app=self)

            for plugin in self.plugins.receive_route:
                plugin.receive_route(finalized_route)

        return routes

    def _iter_handlers(
        self, handlers: Iterable[ControllerRouterHandler], bases: list[Router]
    ) -> Generator[tuple[BaseRouteHandler, list[Router]], None, None]:
        """Recursively iterate over 'handlers', returning tuples of all sub-handlers
        (i.e. handlers included in a Router / Controller) and their preceding layers.

        handlers = [
            Router(
                path="/one",
                route_handlers=[
                    Router(path="/two", route_handlers=[handler_one]),
                    handler_two,
                ],
            )
        ]

        would return:

        [
            (handler_one, [<router path="/two">, <router path="/one">]),
            (handler_two, [<router path="/one">]),
        ]

        """
        for handler in handlers:
            handler = self._validate_registration_value(handler)
            if isinstance(handler, Router):
                yield from self._iter_handlers(handler.route_handlers, bases=[handler, *bases])
            else:
                yield handler, bases

    def _reduce_handlers(self, handlers: Iterable[ControllerRouterHandler]) -> Generator[BaseRouteHandler, None, None]:
        """Reduce possibly nested 'handlers' by recursively iterating over them and their
        sub-handlers (e.g. handlers inside a router), and merging all the options of all
        the layers above into one new handler. This allows us to eliminate all the
        intermediate layers and keep the configuration only on the handlers.

        Using path merging as an example:

        .. code-block:: python

            @get("/handler-one")
            async def handler_one() -> None:
                pass


            @get("/handler-two")
            async def handler_two() -> None:
                pass


            router = Router(
                path="/router-one",
                route_handlers=[
                    handler_one,
                    Router(path="/router-two", route_handlers=[handler_two]),
                ],
            )

        would be the equivalent of writing:

        .. code-block:: python

           @get("/router-one/handler-one")
            async def handler_one() -> None:
                pass

            @get("/router-one/router-two/handler-two")
            async def handler_two() -> None:
                pass
        """
        for handler, bases in self._iter_handlers(handlers, bases=[self]):
            yield handler.merge(*bases)

    def _validate_registration_value(self, value: ControllerRouterHandler) -> RouteHandlerType | Router:
        """Ensure values passed to the register method are supported."""
        from litestar.controller import Controller
        from litestar.handlers import ASGIRouteHandler, WebsocketListener

        if is_class_and_subclass(value, Controller):
            return value().as_router()

        # this narrows down to an ABC, but we assume a non-abstract subclass of the ABC superclass
        if is_class_and_subclass(value, WebsocketListener):
            return value().to_handler()  # pyright: ignore

        if isinstance(value, Router):
            if value is self:
                raise ImproperlyConfiguredException("Cannot register a router on itself")

            return value

        if isinstance(value, (ASGIRouteHandler, HTTPRouteHandler, WebsocketRouteHandler)):
            return value

        raise ImproperlyConfiguredException(
            "Unsupported value passed to `Router.register`. "
            "If you passed in a function or method, "
            "make sure to decorate it first with one of the routing decorators"
        )

    def register(self, value: ControllerRouterHandler) -> None:
        warnings.warn(
            "Registering routes after the application instance has been "
            "created is discouraged, as it might lead to unexpected behaviour "
            "and is a costly operation. To register routes dynamically, a "
            "plugin should be used where routes can be added to the "
            "application via 'AppConfig' 'route_handlers' property",
            category=LitestarWarning,
            stacklevel=2,
        )
        self.routes = []
        self.routes = self._build_routes(
            itertools.chain(
                self._reduce_handlers([value]), (h for route in self.routes for h in get_route_handlers(route))
            )
        )
        self.route_handler_method_map = self._create_route_handler_method_map(self.routes)

        self.asgi_router.construct_routing_trie()

    def get_handler_index_by_name(self, name: str) -> HandlerIndex | None:
        """Receives a route handler name and returns an optional dictionary containing the route handler instance and
        list of paths sorted lexically.

        Examples:
            .. code-block:: python

                from litestar import Litestar, get


                @get("/", name="my-handler")
                def handler() -> None:
                    pass


                app = Litestar(route_handlers=[handler])

                handler_index = app.get_handler_index_by_name("my-handler")

                # { "paths": ["/"], "handler" ... }

        Args:
            name: A route handler unique name.

        Returns:
            A :class:`HandlerIndex <.app.HandlerIndex>` instance or ``None``.
        """
        handler = self.asgi_router.route_handler_index.get(name)
        if not handler:
            return None

        identifier = handler.name or str(handler)
        routes = self.asgi_router.route_mapping[identifier]
        paths = sorted(unique([route.path for route in routes]))

        return HandlerIndex(handler=handler, paths=paths, identifier=identifier)

    def route_reverse(self, name: str, **path_parameters: Any) -> str:
        """Receives a route handler name, path parameter values and returns url path to the handler with filled path
        parameters.

        Examples:
            .. code-block:: python

                from litestar import Litestar, get


                @get("/group/{group_id:int}/user/{user_id:int}", name="get_membership_details")
                def get_membership_details(group_id: int, user_id: int) -> None:
                    pass


                app = Litestar(route_handlers=[get_membership_details])

                path = app.route_reverse("get_membership_details", user_id=100, group_id=10)

                # /group/10/user/100

        Args:
            name: A route handler unique name.
            **path_parameters: Actual values for path parameters in the route. Parameters of type
                `datetime`, `date`, `time`, `timedelta`, `float`, `Path`, `UUID`
                may be passed in their string representations.

        Raises:
            NoRouteMatchFoundException: If route with 'name' does not exist, path parameters are missing in
                ``**path_parameters or have wrong type``.

        Returns:
            A fully formatted url path.
        """
        handler_index = self.get_handler_index_by_name(name)
        if handler_index is None:
            raise NoRouteMatchFoundException(f"Route {name} can not be found")

        allow_str_instead = {datetime, date, time, timedelta, float, Path, UUID}
        routes = sorted(
            self.asgi_router.route_mapping[handler_index["identifier"]],
            key=lambda r: len(r.path_parameters),
            reverse=True,
        )
        passed_parameters = set(path_parameters.keys())

        selected_route = next(
            (route for route in routes if passed_parameters.issuperset(route.path_parameters)),
            routes[-1],
        )
        output: list[str] = []
        for component in selected_route.path_components:
            if isinstance(component, PathParameterDefinition):
                val = path_parameters.get(component.name)
                if not isinstance(val, component.type) and (
                    component.type not in allow_str_instead or not isinstance(val, str)
                ):
                    raise NoRouteMatchFoundException(
                        f"Received type for path parameter {component.name} doesn't match declared type {component.type}"
                    )
                output.append(str(val))
            else:
                output.append(component)

        return join_paths(output)

    def _create_asgi_handler(self) -> ASGIApp:
        """Create an ASGIApp that wraps the ASGI router inside an exception handler.

        If CORS or TrustedHost configs are provided to the constructor, they will wrap the router as well.
        """
        asgi_handler = wrap_in_exception_handler(app=self.asgi_router)

        if self.cors_config:
            asgi_handler = CORSMiddleware(app=asgi_handler, config=self.cors_config)

        try:
            otel_plugin: OpenTelemetryPlugin = self.plugins.get("OpenTelemetryPlugin")
            asgi_handler = otel_plugin.middleware(app=asgi_handler)
        except KeyError:
            pass

        return asgi_handler

    def _wrap_send(self, send: Send, scope: Scope) -> Send:
        """Wrap the ASGI send and handles any 'before send' hooks.

        Args:
            send: The ASGI send function.
            scope: The ASGI scope.

        Returns:
            An ASGI send function.
        """
        if self.before_send:

            async def wrapped_send(message: Message) -> None:
                for hook in self.before_send:
                    await hook(message, scope)
                await send(message)

            return wrapped_send
        return send

    def update_openapi_schema(self) -> None:
        """Update the OpenAPI schema to reflect the route handlers registered on the app.

        Returns:
            None
        """
        self.plugins.get(OpenAPIPlugin)._build_openapi()

    def emit(self, event_id: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event to all attached listeners.

        Args:
            event_id: The ID of the event to emit, e.g ``my_event``.
            args: args to pass to the listener(s).
            kwargs: kwargs to pass to the listener(s)

        Returns:
            None
        """
        self.event_emitter.emit(event_id, *args, **kwargs)


def _maybe_add_options_handler(
    path: str, http_handlers: list[HTTPRouteHandler], root: Router
) -> list[HTTPRouteHandler]:
    handler_methods = {method for handler in http_handlers for method in handler.http_methods}
    if "OPTIONS" not in handler_methods:
        options_handler = create_options_handler(path=path, allow_methods={*handler_methods, "OPTIONS"})  # pyright: ignore
        options_handler = options_handler.merge(root)
        return [*http_handlers, options_handler]
    return http_handlers
