"""Plugin for creating and retrieving flash messages."""

from dataclasses import dataclass
from typing import Any, Mapping

from litestar.config.app import AppConfig
from litestar.connection import ASGIConnection
from litestar.contrib.minijinja import MiniJinjaTemplateEngine
from litestar.plugins import InitPluginProtocol
from litestar.template import TemplateConfig
from litestar.template.base import _get_request_from_context
from litestar.utils.scope.state import ScopeState


@dataclass
class FlashConfig:
    """Configuration for Flash messages."""

    template_config: TemplateConfig


class FlashPlugin(InitPluginProtocol):
    """Flash messages Plugin."""

    def __init__(self, config: FlashConfig):
        """Initialize the plugin.

        Args:
            config: Configuration for flash messages, including the template engine instance.
        """
        self.config = config

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Register the message callable on the template engine instance.

        Args:
            app_config: The application configuration.

        Returns:
            The application configuration with the message callable registered.
        """
        if isinstance(self.config.template_config.engine_instance, MiniJinjaTemplateEngine):
            from litestar.contrib.minijinja import _transform_state

            self.config.template_config.engine_instance.register_template_callable(
                "get_flashes", _transform_state(get_flashes)
            )
        else:
            self.config.template_config.engine_instance.register_template_callable("get_flashes", get_flashes)
        return app_config


def flash(connection: ASGIConnection, message: str, category: str) -> None:
    """Add a flash message to the request scope.

    Args:
        connection: The connection instance.
        message: The message to flash.
        category: The category of the message.
    """
    scope_state = ScopeState.from_scope(connection.scope)
    scope_state.flash_messages.append({"message": message, "category": category})


def get_flashes(context: Mapping[str, Any]) -> Any:
    """Get flash messages from the request scope, if any.

    Args:
        context: The context dictionary.

    Returns:
        The flash messages, if any.
    """
    scope_state = ScopeState.from_scope(_get_request_from_context(context).scope)
    return scope_state.flash_messages
