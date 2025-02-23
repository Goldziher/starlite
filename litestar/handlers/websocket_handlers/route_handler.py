from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from litestar.connection import WebSocket
from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers import BaseRouteHandler
from litestar.types import AsyncAnyCallable, Empty, ParametersMap
from litestar.types.builtin_types import NoneType
from litestar.utils import deprecated
from litestar.utils.predicates import is_async_callable

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from litestar import Litestar, Router
    from litestar._kwargs import KwargsModel
    from litestar._kwargs.cleanup import DependencyCleanupGroup
    from litestar.routes import BaseRoute
    from litestar.types import Dependencies, EmptyType, ExceptionHandler, Guard, Middleware


class WebsocketRouteHandler(BaseRouteHandler):
    __slots__ = ("_kwargs_model", "_websocket_class")

    def __init__(
        self,
        path: str | list[str] | None = None,
        *,
        fn: AsyncAnyCallable,
        dependencies: Dependencies | None = None,
        exception_handlers: dict[int | type[Exception], ExceptionHandler] | None = None,
        guards: Sequence[Guard] | None = None,
        middleware: Sequence[Middleware] | None = None,
        name: str | None = None,
        opt: dict[str, Any] | None = None,
        signature_namespace: Mapping[str, Any] | None = None,
        websocket_class: type[WebSocket] | None = None,
        parameters: ParametersMap | None = None,
        **kwargs: Any,
    ) -> None:
        """Route handler for WebSocket routes.

        Args:
            path: A path fragment for the route handler function or a sequence of path fragments. If not given defaults
                to ``/``
            fn: The handler function

                .. versionadded:: 3.0
            dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
            exception_handlers: A mapping of status codes and/or exception types to handler functions.
            guards: A sequence of :class:`Guard <.types.Guard>` callables.
            middleware: A sequence of :class:`Middleware <.types.Middleware>`.
            name: A string identifying the route handler.
            opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
                wherever you have access to :class:`Request <.connection.Request>` or
                :class:`ASGI Scope <.types.Scope>`.
            signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
            type_encoders: A mapping of types to callables that transform them into types supported for serialization.
            websocket_class: A custom subclass of :class:`WebSocket <.connection.WebSocket>` to be used as route handler's
                default websocket class.
            parameters: A mapping of :func:`Parameter <.params.Parameter>` definitions
            **kwargs: Any additional kwarg - will be set in the opt dictionary.
        """
        self._websocket_class = websocket_class
        self._kwargs_model: KwargsModel | EmptyType = Empty

        super().__init__(
            fn=fn,
            path=path,
            dependencies=dependencies,
            exception_handlers=exception_handlers,
            guards=guards,
            middleware=middleware,
            name=name,
            opt=opt,
            signature_namespace=signature_namespace,
            parameters=parameters,
            **kwargs,
        )

    def _get_merge_opts(self, others: tuple[Router, ...]) -> dict[str, Any]:
        merge_opts = super()._get_merge_opts(others)
        merge_opts["websocket_class"] = self._websocket_class or next(
            (o.websocket_class for o in others if o.websocket_class), None
        )

        return merge_opts

    @deprecated("3.0", removal_in="4.0", alternative=".websocket_class property")
    def resolve_websocket_class(self) -> type[WebSocket]:
        """Return the closest custom WebSocket class in the owner graph or the default Websocket class.

        This method is memoized so the computation occurs only once.

        Returns:
            The default :class:`WebSocket <.connection.WebSocket>` class for the route handler.
        """
        return self.websocket_class

    @property
    def websocket_class(self) -> type[WebSocket]:
        return self._websocket_class or WebSocket

    def _validate_handler_function(self) -> None:
        """Validate the route handler function once it's set by inspecting its return annotations."""
        super()._validate_handler_function()

        if not self.parsed_fn_signature.return_type.is_subclass_of(NoneType):
            raise ImproperlyConfiguredException(f"{self}: WebSocket handlers must return 'None'")

        if "socket" not in self.parsed_fn_signature.parameters:
            raise ImproperlyConfiguredException(f"{self}: WebSocket handlers must define a 'socket' parameter")

        for param in ("request", "body", "data"):
            if param in self.parsed_fn_signature.parameters:
                raise ImproperlyConfiguredException(
                    f"{self}: The {param} kwarg is not supported with websocket handlers"
                )

        if not is_async_callable(self.fn):
            raise ImproperlyConfiguredException(f"{self}: WebSocket handler functions must be asynchronous")

    def on_registration(self, route: BaseRoute, app: Litestar) -> None:
        super().on_registration(route=route, app=app)
        self._kwargs_model = self._create_kwargs_model(path_parameters=route.path_parameters)

    async def handle(self, connection: WebSocket[Any, Any, Any]) -> None:
        """ASGI app that creates a WebSocket from the passed in args, and then awaits the handler function.

        Args:
            connection: WebSocket connection

        Returns:
            None
        """

        handler_kwargs_model = self._kwargs_model
        if handler_kwargs_model is Empty:
            raise ImproperlyConfiguredException("handler parameter model not defined")

        if self.guards:
            await self.authorize_connection(connection=connection)

        parsed_kwargs: dict[str, Any] = {}
        cleanup_group: DependencyCleanupGroup | None = None

        if handler_kwargs_model.has_kwargs:
            parsed_kwargs = await handler_kwargs_model.to_kwargs(connection=connection)

            if handler_kwargs_model.dependency_batches:
                cleanup_group = await handler_kwargs_model.resolve_dependencies(connection, parsed_kwargs)

            parsed_kwargs = self.signature_model.parse_values_from_connection_kwargs(
                connection=connection, kwargs=parsed_kwargs
            )

        if cleanup_group:
            async with cleanup_group:
                await self.fn(**parsed_kwargs)
            await cleanup_group.cleanup()
        else:
            await self.fn(**parsed_kwargs)


def websocket(
    path: str | list[str] | None = None,
    *,
    dependencies: Dependencies | None = None,
    exception_handlers: dict[int | type[Exception], ExceptionHandler] | None = None,
    guards: list[Guard] | None = None,
    middleware: list[Middleware] | None = None,
    name: str | None = None,
    opt: dict[str, Any] | None = None,
    signature_namespace: Mapping[str, Any] | None = None,
    websocket_class: type[WebSocket] | None = None,
    handler_class: type[WebsocketRouteHandler] = WebsocketRouteHandler,
    **kwargs: Any,
) -> Callable[[AsyncAnyCallable], WebsocketRouteHandler]:
    """Create a :class:`WebsocketRouteHandler`.

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments. If not given defaults
            to ``/``
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or
            :class:`ASGI Scope <.types.Scope>`.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        websocket_class: A custom subclass of :class:`WebSocket <.connection.WebSocket>` to be used as route handler's
            default websocket class.
        handler_class: Route handler class instantiated by the decorator
        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AsyncAnyCallable) -> WebsocketRouteHandler:
        return handler_class(
            path=path,
            fn=fn,
            dependencies=dependencies,
            exception_handlers=exception_handlers,
            guards=guards,
            middleware=middleware,
            name=name,
            opt=opt,
            signature_namespace=signature_namespace,
            websocket_class=websocket_class,
            **kwargs,
        )

    return decorator
