from __future__ import annotations

import functools
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, NoReturn, cast

from litestar._signature import SignatureModel
from litestar.di import Provide
from litestar.dto import DTOData
from litestar.exceptions import ImproperlyConfiguredException, LitestarException
from litestar.router import Router
from litestar.serialization import default_deserializer, default_serializer
from litestar.types import (
    Dependencies,
    Empty,
    ExceptionHandlersMap,
    Guard,
    Middleware,
    ParametersMap,
    TypeDecodersSequence,
    TypeEncodersMap,
)
from litestar.typing import FieldDefinition
from litestar.utils import ensure_async_callable, get_name, join_paths, normalize_path
from litestar.utils.deprecation import deprecated
from litestar.utils.empty import value_or_default
from litestar.utils.helpers import unwrap_partial
from litestar.utils.signature import ParsedSignature, add_types_to_signature_namespace, merge_signature_namespaces

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from typing_extensions import Self

    from litestar._kwargs import KwargsModel
    from litestar.app import Litestar
    from litestar.connection import ASGIConnection
    from litestar.dto import AbstractDTO
    from litestar.routes import BaseRoute
    from litestar.types import AsyncAnyCallable
    from litestar.types.callable_types import AnyCallable, AsyncGuard
    from litestar.types.empty import EmptyType

__all__ = ("BaseRouteHandler",)


class BaseRouteHandler:
    """Base route handler.

    Serves as a subclass for all route handlers
    """

    __slots__ = (
        "_dto",
        "_parameter_field_definitions",
        "_parsed_data_field",
        "_parsed_fn_signature",
        "_parsed_return_field",
        "_resolved_signature_model",
        "_return_dto",
        "dependencies",
        "exception_handlers",
        "fn",
        "guards",
        "middleware",
        "name",
        "opt",
        "parameters",
        "paths",
        "signature_namespace",
        "type_decoders",
        "type_encoders",
    )

    def __init__(
        self,
        path: str | Sequence[str] | None = None,
        *,
        fn: AsyncAnyCallable,
        dependencies: Dependencies | None = None,
        dto: type[AbstractDTO] | None | EmptyType = Empty,
        exception_handlers: ExceptionHandlersMap | None = None,
        guards: Sequence[Guard] | None = None,
        middleware: Sequence[Middleware] | None = None,
        name: str | None = None,
        opt: Mapping[str, Any] | None = None,
        return_dto: type[AbstractDTO] | None | EmptyType = Empty,
        signature_namespace: Mapping[str, Any] | None = None,
        signature_types: Sequence[Any] | None = None,
        parameters: ParametersMap | None = None,
        type_decoders: TypeDecodersSequence | None = None,
        type_encoders: TypeEncodersMap | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize ``HTTPRouteHandler``.

        Args:
            path: A path fragment for the route handler function or a sequence of path fragments. If not given defaults
                to ``/``
            fn: The handler function

                .. versionadded:: 3.0
            dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
            dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for (de)serializing and
                validation of request data.
            exception_handlers: A mapping of status codes and/or exception types to handler functions.
            guards: A sequence of :class:`Guard <.types.Guard>` callables.
            middleware: A sequence of :class:`Middleware <.types.Middleware>`.
            name: A string identifying the route handler.
            opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
                wherever you have access to :class:`Request <.connection.Request>` or
                :class:`ASGI Scope <.types.Scope>`.
            return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing
                outbound response data.
            signature_namespace: A mapping of names to types for use in forward reference resolution during signature
                modelling.
            signature_types: A sequence of types for use in forward reference resolution during signature modeling.
                These types will be added to the signature namespace using their ``__name__`` attribute.
            type_decoders: A sequence of tuples, each composed of a predicate testing for type identity and a msgspec hook for deserialization.
            type_encoders: A mapping of types to callables that transform them into types supported for serialization.
            parameters: A mapping of :func:`Parameter <.params.Parameter>` definitions
            **kwargs: Any additional kwarg - will be set in the opt dictionary.
        """
        self._parsed_fn_signature: ParsedSignature | EmptyType = Empty
        self._parsed_return_field: FieldDefinition | EmptyType = Empty
        self._parsed_data_field: FieldDefinition | None | EmptyType = Empty
        self._parameter_field_definitions: dict[str, FieldDefinition] | EmptyType = Empty
        self._resolved_signature_model: type[SignatureModel] | EmptyType = Empty

        self.dependencies = (
            {
                key: provider if isinstance(provider, Provide) else Provide(provider)
                for key, provider in dependencies.items()
            }
            if dependencies
            else {}
        )
        self._dto = dto
        self._return_dto = return_dto
        self.exception_handlers = exception_handlers or {}
        self.guards: tuple[AsyncGuard, ...] = tuple(ensure_async_callable(guard) for guard in guards) if guards else ()
        self.middleware = tuple(middleware) if middleware else ()
        self.name = name
        self.opt = dict(opt or {})
        self.opt.update(**kwargs)
        self.signature_namespace = add_types_to_signature_namespace(
            signature_types or [], dict(signature_namespace or {})
        )
        self.type_decoders = type_decoders or ()
        self.type_encoders = type_encoders or {}
        self.paths = (
            {normalize_path(p) for p in path} if path and isinstance(path, list) else {normalize_path(path or "/")}  # type: ignore[arg-type]
        )
        self.fn = fn
        self.parameters = parameters or {}

    def _get_merge_opts(self, others: tuple[Router, ...]) -> dict[str, Any]:
        """Get kwargs for .merge.

        This is effectively the same as doing:

        for other in others:
            handler = handler.merge(other)

        The downside of that approach is that it creates a bunch of intermediate
        instances requires every subclass that adds properties to re-implement all the
        merging logic.
        With this approach, the subclass can instead override this method, call
        super()._get_merge_opts(), and extend the dict returned by it.

        The downside here is that we don't get type safety (as long as annotating
        **kwargs with TypedDicts isn't supported anyway).

        The plan is for this to go away in version 4, where we can move to fully static
        handler config, separating the logic and configuration entirely.
        """
        path = (
            functools.reduce(
                lambda a, b: join_paths([a, b]),
                (o.path for o in reversed(others)),
            )
            if others
            else ""
        )
        merge_opts: dict[str, Any] = {
            "fn": self.fn,
            "name": self.name,
            "path": [join_paths([path, p]) for p in self.paths],
        }

        other: BaseRouteHandler | Router
        for other in (self, *others):  # type: ignore[assignment]
            merge_opts["dependencies"] = {**other.dependencies, **merge_opts.get("dependencies", {})}
            merge_opts["exception_handlers"] = {**other.exception_handlers, **merge_opts.get("exception_handlers", {})}
            merge_opts["guards"] = (*other.guards, *merge_opts.get("guards", ()))

            merge_opts["middleware"] = (*other.middleware, *merge_opts.get("middleware", ()))
            merge_opts["opt"] = {**other.opt, **merge_opts.get("opt", {})}
            merge_opts["type_decoders"] = (*merge_opts.get("type_decoders", ()), *other.type_decoders)
            merge_opts["type_encoders"] = {**merge_opts.get("type_encoders", {}), **other.type_encoders}
            merge_opts["parameters"] = {**merge_opts.get("parameters", {}), **other.parameters}
            merge_opts["signature_namespace"] = merge_signature_namespaces(
                merge_opts.get("signature_namespace", {}), other.signature_namespace
            )

            # '.dto' on the router is the dto config value supplied by the users,
            # whereas '.dto' on the handler is the fully resolved dto. The dto config on
            # the handler is stored under '._dto', so we have to do this little workaround
            if other is not self:
                other = cast(Router, other)  # mypy cannot narrow with the 'is not self' check
                merge_opts["dto"] = value_or_default(merge_opts.get("dto", Empty), other.dto)
                merge_opts["return_dto"] = value_or_default(merge_opts.get("return_dto", Empty), other.return_dto)

        merge_opts["dto"] = value_or_default(self._dto, merge_opts.get("dto", Empty))
        merge_opts["return_dto"] = value_or_default(self._return_dto, merge_opts.get("return_dto", Empty))

        # due to the way we're traversing over the app layers, the middleware stack is
        # constructed in the wrong order (handler > application). reversing the order
        # here is easier than handling it correctly at every intermediary step.
        #
        # we only call this if 'others' is non-empty, to ensure we don't change anything
        # if no layers have been merged (happens in '._with_changes' for example)
        if others:
            merge_opts["middleware"] = tuple(reversed(merge_opts["middleware"]))

        return merge_opts

    def _with_changes(self, **kwargs: Any) -> Self:
        """Return a new instance of the handler, replacing attributes specified in **kwargs"""
        opts = self._get_merge_opts(())
        opts.update(kwargs)
        return type(self)(**opts)

    def merge(self, *others: Router) -> Self:
        return type(self)(**self._get_merge_opts(others))

    @property
    def handler_id(self) -> str:
        """A unique identifier used for generation of DTOs."""
        return f"{self!s}::{id(self)}"

    @property
    def default_deserializer(self) -> Callable[[Any, Any], Any]:
        """Get a default deserializer for the route handler.

        Returns:
            A default deserializer for the route handler.

        """
        return partial(default_deserializer, type_decoders=self.type_decoders)

    @property
    def default_serializer(self) -> Callable[[Any], Any]:
        """Get a default serializer for the route handler.

        Returns:
            A default serializer for the route handler.

        """
        return partial(default_serializer, type_encoders=self.type_encoders)

    @property
    def signature_model(self) -> type[SignatureModel]:
        """Get the signature model for the route handler.

        Returns:
            A signature model for the route handler.

        """
        if self._resolved_signature_model is Empty:
            self._resolved_signature_model = SignatureModel.create(
                dependency_name_set=set(self.dependencies.keys()),
                fn=cast("AnyCallable", self.fn),
                parsed_signature=self.parsed_fn_signature,
                data_dto=self.data_dto,
                type_decoders=self.type_decoders,
            )
        return self._resolved_signature_model

    @property
    def parsed_fn_signature(self) -> ParsedSignature:
        """Return the parsed signature of the handler function.

        This method is memoized so the computation occurs only once.

        Returns:
            A ParsedSignature instance
        """
        if self._parsed_fn_signature is Empty:
            self._parsed_fn_signature = ParsedSignature.from_fn(unwrap_partial(self.fn), self.signature_namespace)

        return self._parsed_fn_signature

    @property
    def parsed_return_field(self) -> FieldDefinition:
        if self._parsed_return_field is Empty:
            self._parsed_return_field = self.parsed_fn_signature.return_type
        return self._parsed_return_field

    @property
    def parsed_data_field(self) -> FieldDefinition | None:
        if self._parsed_data_field is Empty:
            self._parsed_data_field = self.parsed_fn_signature.parameters.get("data")
        return self._parsed_data_field

    @property
    def handler_name(self) -> str:
        """Get the name of the handler function.

        Raises:
            ImproperlyConfiguredException: if handler fn is not set.

        Returns:
            Name of the handler function
        """
        return get_name(unwrap_partial(self.fn))

    def _raise_not_registered(self) -> NoReturn:
        raise LitestarException(
            f"Handler {self!r}: Accessing this attribute is unsafe until the handler has been "
            "registered with an application, as it may yield different results after registration."
        )

    @deprecated("3.0", removal_in="4.0", alternative=".type_encoders attribute")
    def resolve_type_encoders(self) -> TypeEncodersMap:
        """Return a merged type_encoders mapping.

        Returns:
            A dict of type encoders
        """

        return self.type_encoders

    @deprecated("3.0", removal_in="4.0", alternative=".type_decoders attribute")
    def resolve_type_decoders(self) -> TypeDecodersSequence:
        """Return a merged type_encoders mapping.

        Returns:
            A dict of type encoders
        """

        return self.type_decoders

    @deprecated("3.0", removal_in="4.0", alternative=".parameter_field_definitions property")
    def resolve_layered_parameters(self) -> dict[str, FieldDefinition]:
        return self.parameter_field_definitions

    @property
    def parameter_field_definitions(self) -> dict[str, FieldDefinition]:
        """Return all parameters declared above the handler."""
        if self._parameter_field_definitions is Empty:
            self._parameter_field_definitions = {
                key: FieldDefinition.from_kwarg(name=key, annotation=parameter.annotation, kwarg_definition=parameter)
                for key, parameter in self.parameters.items()
            }
        return self._parameter_field_definitions

    @deprecated("3.0", removal_in="4.0", alternative=".guards attribute")
    def resolve_guards(self) -> tuple[Guard, ...]:
        """Return all guards in the handlers scope, starting from highest to current layer."""

        return self.guards

    @deprecated("3.0", removal_in="4.0", alternative=".dependencies attribute")
    def resolve_dependencies(self) -> dict[str, Provide]:
        """Return all dependencies correlating to handler function's kwargs that exist in the handler's scope."""

        return self.dependencies

    def _finalize_dependencies(self, app: Litestar) -> None:
        dependencies: dict[str, Provide] = {}

        # keep track of which providers are available for each dependency
        provider_keys: dict[Any, str] = {}

        for key, provider in self.dependencies.items():
            # ensure that if a provider for this dependency has already been registered,
            # registering this provider again is only allowed as an override, i.e. with
            # the same key
            if (existing_key := provider_keys.get(provider.dependency)) and existing_key != key:
                raise ImproperlyConfiguredException(
                    f"Provider for {provider.dependency!r} with key {key!r} is already defined under a different key "
                    f"{existing_key!r}. If you wish to override a provider, it must have the same key."
                )

            provider.finalize(
                plugins=app.plugins,
                signature_namespace=self.signature_namespace,
                data_dto=self.data_dto,
                dependency_keys=set(self.dependencies),
                type_decoders=self.type_decoders,
            )
            provider_keys[provider.dependency] = key
            dependencies[key] = provider

    @deprecated("3.0", removal_in="4.0", alternative=".middleware attribute")
    def resolve_middleware(self) -> tuple[Middleware, ...]:
        """Return registered middlewares"""

        return self.middleware

    @deprecated("3.0", removal_in="4.0", alternative=".exception_handlers attribute")
    def resolve_exception_handlers(self) -> ExceptionHandlersMap:
        """Resolve the exception_handlers by starting from the route handler and moving up.

        This method is memoized so the computation occurs only once.
        """

        return self.exception_handlers

    @deprecated("3.0", removal_in="4.0", alternative=".signature_namespace attribute")
    def resolve_signature_namespace(self) -> dict[str, Any]:
        """Build the route handler signature namespace dictionary by going from top to bottom"""

        return self.signature_namespace

    @property
    def data_dto(self) -> type[AbstractDTO] | None:
        if self._dto is Empty:
            self._raise_not_registered()
        return self._dto

    @deprecated("3.0", removal_in="4.0", alternative=".data_dto attribute")
    def resolve_data_dto(self) -> type[AbstractDTO] | None:
        return self.data_dto

    def _resolve_data_dto(self, app: Litestar) -> type[AbstractDTO] | None:
        """Resolve the data_dto by starting from the route handler and moving up.
        If a handler is found it is returned, otherwise None is set.
        This method is memoized so the computation occurs only once.

        Returns:
            An optional :class:`DTO type <.dto.base_dto.AbstractDTO>`
        """
        data_dto: type[AbstractDTO] | None = None
        if (_data_dto := self._dto) is not Empty:
            data_dto = _data_dto
        elif self.parsed_data_field and (
            plugin_for_data_type := next(
                (
                    plugin
                    for plugin in app.plugins.serialization
                    if self.parsed_data_field.match_predicate_recursively(plugin.supports_type)
                ),
                None,
            )
        ):
            data_dto = plugin_for_data_type.create_dto_for_type(self.parsed_data_field)

        if self.parsed_data_field and data_dto:
            data_dto.create_for_field_definition(
                field_definition=self.parsed_data_field,
                handler_id=self.handler_id,
            )

        return data_dto

    @property
    def return_dto(self) -> type[AbstractDTO] | None:
        if self._return_dto is Empty:
            self._raise_not_registered()
        return self._return_dto

    @deprecated("3.0", removal_in="4.0", alternative=".return_dto attribute")
    def resolve_return_dto(self) -> type[AbstractDTO] | None:
        return self.return_dto

    def _resolve_return_dto(self, app: Litestar, data_dto: type[AbstractDTO] | None) -> type[AbstractDTO] | None:
        """Resolve the return_dto by starting from the route handler and moving up.
        If a handler is found it is returned, otherwise None is set.
        This method is memoized so the computation occurs only once.

        Returns:
            An optional :class:`DTO type <.dto.base_dto.AbstractDTO>`
        """
        if (_return_dto := self._return_dto) is not Empty:
            return_dto: type[AbstractDTO] | None = _return_dto
        elif plugin_for_return_type := next(
            (
                plugin
                for plugin in app.plugins.serialization
                if self.parsed_return_field.match_predicate_recursively(plugin.supports_type)
            ),
            None,
        ):
            return_dto = plugin_for_return_type.create_dto_for_type(self.parsed_return_field)
        else:
            return_dto = data_dto

        if return_dto and return_dto.is_supported_model_type_field(self.parsed_return_field):
            return_dto.create_for_field_definition(
                field_definition=self.parsed_return_field,
                handler_id=self.handler_id,
            )
            resolved_return_dto = return_dto
        else:
            resolved_return_dto = None

        return resolved_return_dto

    async def authorize_connection(self, connection: ASGIConnection) -> None:
        """Ensure the connection is authorized by running all the route guards in scope."""
        for guard in self.guards:
            await guard(connection, self)

    def on_registration(self, route: BaseRoute, app: Litestar) -> None:
        """Called once per handler when the app object is instantiated.

        Args:
            route: The route this handler is being registered on
            app: The application instance

        Returns:
            None
        """

        self._dto = self._resolve_data_dto(app=app)
        self._return_dto = self._resolve_return_dto(app=app, data_dto=self._dto)

        self._validate_handler_function()
        self._finalize_dependencies(app=app)

    def _validate_handler_function(self) -> None:
        """Validate the route handler function once set by inspecting its return annotations."""
        if self.parsed_data_field is not None and self.parsed_data_field.is_subclass_of(DTOData) and not self.data_dto:
            raise ImproperlyConfiguredException(
                f"Handler function {self.handler_name} has a data parameter that is a subclass of DTOData but no "
                "DTO has been registered for it."
            )

    def __str__(self) -> str:
        """Return a unique identifier for the route handler.

        Returns:
            A string
        """
        target: type[AsyncAnyCallable] | AsyncAnyCallable  # pyright: ignore
        target = unwrap_partial(self.fn)
        if not hasattr(target, "__qualname__"):
            target = type(target)
        return f"{target.__module__}.{target.__qualname__}"

    def _create_kwargs_model(
        self,
        path_parameters: Iterable[str],
    ) -> KwargsModel:
        """Create a `KwargsModel` for a given route handler."""
        from litestar._kwargs import KwargsModel

        return KwargsModel.create_for_signature_model(
            signature_model=self.signature_model,
            parsed_signature=self.parsed_fn_signature,
            dependencies=self.dependencies,
            path_parameters=set(path_parameters),
            layered_parameters=self.parameter_field_definitions,
        )
