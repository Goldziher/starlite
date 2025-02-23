from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Callable

from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers.base import BaseRouteHandler
from litestar.types.builtin_types import NoneType
from litestar.utils.predicates import is_async_callable

__all__ = ("ASGIRouteHandler", "asgi")


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from litestar import Litestar, Router
    from litestar.connection import ASGIConnection
    from litestar.routes import BaseRoute
    from litestar.types import (
        AsyncAnyCallable,
        ExceptionHandlersMap,
        Guard,
        ParametersMap,
    )


class ASGIRouteHandler(BaseRouteHandler):
    __slots__ = (
        "copy_scope",
        "is_mount",
    )

    def __init__(
        self,
        path: str | Sequence[str] | None = None,
        *,
        fn: AsyncAnyCallable,
        exception_handlers: ExceptionHandlersMap | None = None,
        guards: Sequence[Guard] | None = None,
        name: str | None = None,
        opt: Mapping[str, Any] | None = None,
        is_mount: bool = False,
        signature_namespace: Mapping[str, Any] | None = None,
        copy_scope: bool | None = None,
        parameters: ParametersMap | None = None,
        **kwargs: Any,
    ) -> None:
        """Route handler for ASGI routes.

        Args:
            path: A path fragment for the route handler function or a list of path fragments. If not given defaults to
                ``/``.
            fn: The handler function.

                .. versionadded:: 3.0
            exception_handlers: A mapping of status codes and/or exception types to handler functions.
            guards: A sequence of :class:`Guard <.types.Guard>` callables.
            name: A string identifying the route handler.
            opt: A string key mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
                wherever you have access to :class:`Request <.connection.Request>` or
                :class:`ASGI Scope <.types.Scope>`.
            is_mount: A boolean dictating whether the handler's paths should be regarded as mount paths. Mount path
                accept any arbitrary paths that begin with the defined prefixed path. For example, a mount with the path
                ``/some-path/`` will accept requests for ``/some-path/`` and any sub path under this, e.g.
                ``/some-path/sub-path/`` etc.
            signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
            type_encoders: A mapping of types to callables that transform them into types supported for serialization.
            copy_scope: Copy the ASGI 'scope' before calling the mounted application. Should be set to 'True' unless
                side effects via scope mutations by the mounted ASGI application are intentional
            parameters: A mapping of :func:`Parameter <.params.Parameter>` definitions
            **kwargs: Any additional kwarg - will be set in the opt dictionary.
        """
        self.is_mount = is_mount
        self.copy_scope = copy_scope

        super().__init__(
            path,
            fn=fn,
            exception_handlers=exception_handlers,
            guards=guards,
            name=name,
            opt=opt,
            signature_namespace=signature_namespace,
            parameters=parameters,
            **kwargs,
        )

    def on_registration(self, route: BaseRoute, app: Litestar) -> None:
        super().on_registration(app=app, route=route)

        if self.copy_scope is None:
            warnings.warn(
                f"{self}: 'copy_scope' not set for ASGI handler. Leaving 'copy_scope' unset will warn about mounted "
                "ASGI applications modifying the scope. Set 'copy_scope=True' to ensure calling into mounted ASGI apps "
                "does not cause any side effects via scope mutations, or set 'copy_scope=False' if those mutations are "
                "desired. 'copy'scope' will default to 'True' in Litestar 3",
                category=DeprecationWarning,
                stacklevel=1,
            )

    def _get_merge_opts(self, others: tuple[Router, ...]) -> dict[str, Any]:
        merge_opts = super()._get_merge_opts(others)
        merge_opts["is_mount"] = self.is_mount
        merge_opts["copy_scope"] = self.copy_scope
        return merge_opts

    def _validate_handler_function(self) -> None:
        """Validate the route handler function once it's set by inspecting its return annotations."""
        super()._validate_handler_function()

        if not self.parsed_fn_signature.return_type.is_subclass_of(NoneType):
            raise ImproperlyConfiguredException("ASGI handler functions should return 'None'")

        if any(key not in self.parsed_fn_signature.parameters for key in ("scope", "send", "receive")):
            raise ImproperlyConfiguredException(
                "ASGI handler functions should define 'scope', 'send' and 'receive' arguments"
            )
        if not is_async_callable(self.fn):
            raise ImproperlyConfiguredException("Functions decorated with 'asgi' must be async functions")

    async def handle(self, connection: ASGIConnection[ASGIRouteHandler, Any, Any, Any]) -> None:
        """ASGI app that authorizes the connection and then awaits the handler function.

        .. versionadded: 3.0

        Args:
                connection: The ASGI connection

        Returns:
                None
        """

        if self.guards:
            await self.authorize_connection(connection=connection)

        await self.fn(scope=connection.scope, receive=connection.receive, send=connection.send)


def asgi(
    path: str | Sequence[str] | None = None,
    *,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    name: str | None = None,
    opt: Mapping[str, Any] | None = None,
    is_mount: bool = False,
    signature_namespace: Mapping[str, Any] | None = None,
    handler_class: type[ASGIRouteHandler] = ASGIRouteHandler,
    **kwargs: Any,
) -> Callable[[AsyncAnyCallable], ASGIRouteHandler]:
    """Create an :class:`ASGIRouteHandler`.

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments. If not given defaults
            to ``/``
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or
            :class:`ASGI Scope <.types.Scope>`.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature
            modelling.
        is_mount: A boolean dictating whether the handler's paths should be regarded as mount paths. Mount path
            accept any arbitrary paths that begin with the defined prefixed path. For example, a mount with the path
            ``/some-path/`` will accept requests for ``/some-path/`` and any sub path under this, e.g.
            ``/some-path/sub-path/`` etc.
        handler_class: Route handler class instantiated by the decorator
        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: AsyncAnyCallable) -> ASGIRouteHandler:
        return handler_class(
            fn=fn,
            path=path,
            exception_handlers=exception_handlers,
            guards=guards,
            name=name,
            opt=opt,
            is_mount=is_mount,
            signature_namespace=signature_namespace,
            **kwargs,
        )

    return decorator
