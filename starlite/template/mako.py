from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple, Union

from starlite.exceptions import MissingDependencyException, TemplateNotFoundException
from starlite.template.base import (
    TemplateEngineProtocol,
    TemplateProtocol,
    csrf_token,
    url_for,
)

try:
    from mako.exceptions import TemplateLookupException as MakoTemplateNotFound
    from mako.lookup import TemplateLookup

except ImportError as e:
    raise MissingDependencyException("mako is not installed") from e

if TYPE_CHECKING:
    from mako.template import Template as _MakoTemplate
    from pydantic import DirectoryPath


class MakoTemplate(TemplateProtocol):
    def __init__(
        self, template: "_MakoTemplate", template_callables: List[Tuple[str, Callable[[Dict[str, Any]], Any]]]
    ):
        super().__init__()
        self.template = template
        self.template_callables = template_callables

    def render(self, *args: Any, **kwargs: Any) -> str:
        for callable_key, template_callable in self.template_callables:
            kwargs_copy = {**kwargs}
            kwargs[callable_key] = partial(template_callable, kwargs_copy)
        return str(self.template.render(*args, **kwargs))


class MakoTemplateEngine(TemplateEngineProtocol[MakoTemplate]):
    def __init__(self, directory: Union["DirectoryPath", List["DirectoryPath"]]) -> None:
        """Mako based TemplateEngine.

        Args:
            directory: Direct path or list of directory paths from which to serve templates.
        """
        super().__init__(directory=directory)
        self.engine = TemplateLookup(directories=directory if isinstance(directory, (list, tuple)) else [directory])
        self._template_callables: List[Tuple[str, Callable[[Dict[str, Any]], Any]]] = []
        self.register_template_callable(key="url_for", template_callable=url_for)  # type: ignore
        self.register_template_callable(key="csrf_token", template_callable=csrf_token)  # type: ignore

    def get_template(self, template_name: str) -> MakoTemplate:
        """
        Retrieves a template by matching its name (dotted path) with files in the directory or directories provided.
        Args:
            template_name: A dotted path

        Returns:
            MakoTemplate instance

        Raises:
            [TemplateNotFoundException][starlite.exceptions.TemplateNotFoundException]: if no template is found.
        """
        try:
            return MakoTemplate(
                template=self.engine.get_template(template_name), template_callables=self._template_callables
            )
        except MakoTemplateNotFound as exc:
            raise TemplateNotFoundException(template_name=template_name) from exc

    def register_template_callable(self, key: str, template_callable: Callable[[Dict[str, Any]], Any]) -> None:
        """Registers a callable on the template engine.

        Args:
            key: The callable key, i.e. the value to use inside the template to call the callable.
            template_callable: A callable to register.

        Returns:
            None
        """
        self._template_callables.append((key, template_callable))
