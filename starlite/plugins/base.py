from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import Protocol, get_args, runtime_checkable

if TYPE_CHECKING:
    from pydantic import BaseModel

    from starlite.types import (
        AfterRequestHandler,
        AfterResponseHandler,
        BeforeRequestHandler,
        ControllerRouterHandler,
        Dependencies,
        ExceptionHandlersMap,
        Guard,
        LifeCycleHandler,
        Middleware,
        ParametersMap,
        ResponseCookies,
        ResponseHeadersMap,
        ResponseType,
    )

ModelT = TypeVar("ModelT")


@runtime_checkable
class PluginProtocol(Protocol[ModelT]):  # pragma: no cover
    def provide_route_handlers(self) -> List["ControllerRouterHandler"]:
        return []

    def provide_on_startup_handlers(self, on_startup: List["LifeCycleHandler"]) -> List["LifeCycleHandler"]:
        return on_startup

    def provide_on_shutdown_handlers(self, on_shutdown: List["LifeCycleHandler"]) -> List["LifeCycleHandler"]:
        return on_shutdown

    def provide_after_request(self) -> Optional["AfterRequestHandler"]:
        return None

    def provide_before_request(self) -> Optional["BeforeRequestHandler"]:
        return None

    def provide_after_response(self) -> Optional["AfterResponseHandler"]:
        return None

    def provide_exception_handlers(self) -> "ExceptionHandlersMap":
        return {}

    def provide_guards(self) -> List["Guard"]:
        return []

    def provide_middlewares(self, middlewares: List["Middleware"]) -> List["Middleware"]:
        """Receives the list of user provided middlewares and returns an
        updated list of middlewares. This is intended to allow the plugin to
        determine the order of insertion of middlewares.

        Args:
            middlewares: The list of user provided middlewares provided on the Starlite app constructor
                (i.e. app 'level' middlewares).
        Returns:
            An updates list of middlewares.
        """
        return middlewares

    def provide_dependencies(self) -> "Dependencies":
        """Provides dependencies to the application. Any .

        Returns: A string keyed dictionary of dependency [Provider][starlite.provide.Provide] instances.
        """
        return {}

    def provide_parameters(self) -> "ParametersMap":
        return {}

    def provide_response_class(self) -> Optional["ResponseType"]:
        return None

    def provide_response_headers(self) -> "ResponseHeadersMap":
        return {}

    def provide_response_cookies(self) -> "ResponseCookies":
        return []

    def provide_openapi_tags(self) -> List[str]:
        return []

    @staticmethod
    def is_plugin_supported_type(value: Any) -> bool:
        """Given a value of indeterminate type, determine if this value is
        supported by the plugin."""
        return False

    def to_pydantic_model_class(self, model_class: Type[ModelT], **kwargs: Any) -> Type["BaseModel"]:
        """Given a model_class T, convert it to a subclass of the pydantic
        BaseModel."""
        raise NotImplementedError()

    def from_pydantic_model_instance(self, model_class: Type[ModelT], pydantic_model_instance: "BaseModel") -> ModelT:
        """Given an instance of a pydantic model created using a plugin's
        'to_pydantic_model_class', return an instance of the class from which
        that pydantic model has been created.

        This class is passed in as the 'model_class' kwarg.
        """
        raise NotImplementedError()

    def to_dict(self, model_instance: ModelT) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Given an instance of a model supported by the plugin, return a
        dictionary of serializable values."""
        raise NotImplementedError()

    def from_dict(self, model_class: Type[ModelT], **kwargs: Any) -> ModelT:
        """Given a class supported by this plugin and a dict of values, create
        an instance of the class."""
        raise NotImplementedError()


def get_plugin_for_value(value: Any, plugins: List[PluginProtocol]) -> Optional[PluginProtocol]:
    """Helper function to return a plugin for handling the given value, if any
    plugin supports it."""
    if plugins:
        if value and isinstance(value, (list, tuple)):
            value = value[0]
        if get_args(value):
            value = get_args(value)[0]
        for plugin in plugins:
            if plugin.is_plugin_supported_type(value):
                return plugin
    return None


class PluginMapping(NamedTuple):
    plugin: PluginProtocol
    model_class: Any

    def get_model_instance_for_value(
        self, value: Union["BaseModel", List["BaseModel"], Tuple["BaseModel", ...]]
    ) -> Any:
        """Given a value generated by plugin, return an instance of the
        original class.

        Can also accept a list or tuple of values.
        """
        if isinstance(value, (list, tuple)):
            return [
                self.plugin.from_pydantic_model_instance(self.model_class, pydantic_model_instance=item)
                for item in value
            ]
        return self.plugin.from_pydantic_model_instance(self.model_class, pydantic_model_instance=value)
