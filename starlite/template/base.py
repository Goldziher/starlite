from typing import TYPE_CHECKING, Any, List, TypeVar, Union

from pydantic import DirectoryPath, validate_arguments
from typing_extensions import Protocol, TypedDict, runtime_checkable

from starlite.utils import generate_csrf_token

if TYPE_CHECKING:
    from starlite import Request


class TemplateContext(TypedDict):
    request: "Request[Any, Any]"


def url_for(context: TemplateContext, route_name: str, **path_parameters: Any) -> str:
    """Wrapper for [route_reverse][starlite.app.route_reverse] to be used in
    templates.

    Args:
        context: The template context.
        route_name: The name of the route handler.
        **path_parameters: Actual values for path parameters in the route.

    Raises:
        NoRouteMatchFoundException: If path parameters are missing in **path_parameters or have wrong type.

    Returns:
        A fully formatted url path.
    """
    return context["request"].app.route_reverse(route_name, **path_parameters)


def csrf_token(context: TemplateContext) -> str:
    """Sets a CSRF token on the template.

    Notes:
        - to use this function make sure to pass an instance of [CSRFConfig][starlite.config.csrf_config.CSRFConfig] to
        the [Starlite][starlite.app.Starlite] constructor.

    Args:
        context: The template context.


    Returns:
        A CSRF token if the app level `csrf_config` is set, otherwise an empty string.
    """
    csrf_config = context["request"].app.csrf_config
    return generate_csrf_token(csrf_config.secret) if csrf_config else ""


class TemplateProtocol(Protocol):  # pragma: no cover
    """Protocol Defining a 'Template'.

    Template is a class that has a render method which renders the
    template into a string.
    """

    def render(self, *args: Any, **kwargs: Any) -> str:
        """Returns the rendered template as a string.

        Args:
            **kwargs: A string keyed mapping of values passed to the TemplateEngine

        Returns:
            The rendered template string
        """
        ...


T_co = TypeVar("T_co", bound=TemplateProtocol, covariant=True)


@runtime_checkable
class TemplateEngineProtocol(Protocol[T_co]):  # pragma: no cover
    @validate_arguments
    def __init__(self, directory: Union[DirectoryPath, List[DirectoryPath]]) -> None:
        """Protocol for a templating engine.

        Args:
            directory: Direct path or list of directory paths from which to serve templates.
        """
        ...

    def get_template(self, template_name: str) -> T_co:
        """
        Retrieves a template by matching its name (dotted path) with files in the directory or directories provided.
        Args:
            template_name: A dotted path

        Returns:
            Template instance

        Raises:
            [TemplateNotFoundException][starlite.exceptions.TemplateNotFoundException]: if no template is found.
        """
        ...
