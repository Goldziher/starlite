from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from click import Group

from litestar import Litestar, MediaType, get
from litestar.constants import UNDEFINED_SENTINELS
from litestar.contrib.attrs import AttrsSchemaPlugin
from litestar.contrib.pydantic import PydanticDIPlugin, PydanticInitPlugin, PydanticPlugin, PydanticSchemaPlugin
from litestar.contrib.sqlalchemy.plugins import SQLAlchemySerializationPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol, OpenAPISchemaPlugin, PluginRegistry
from litestar.plugins.core import MsgspecDIPlugin
from litestar.testing import create_test_client
from litestar.typing import FieldDefinition

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


def test_plugin_on_app_init() -> None:
    @get("/", media_type=MediaType.TEXT)
    def greet() -> str:
        return "hello world"

    tag = "on_app_init_called"

    def on_startup(app: Litestar) -> None:
        app.state.called = True

    class PluginWithInitOnly(InitPluginProtocol):
        def on_app_init(self, app_config: AppConfig) -> AppConfig:
            app_config.tags.append(tag)
            app_config.on_startup.append(on_startup)
            app_config.route_handlers.append(greet)
            return app_config

    with create_test_client(plugins=[PluginWithInitOnly()]) as client:
        response = client.get("/")
        assert response.text == "hello world"

        assert tag in client.app.tags
        assert client.app.state.called


def test_plugin_registry() -> None:
    class CLIPlugin(CLIPluginProtocol):
        def on_cli_init(self, cli: Group) -> None:
            pass

    cli_plugin = CLIPlugin()
    serialization_plugin = SQLAlchemySerializationPlugin()
    openapi_plugin = PydanticSchemaPlugin()
    init_plugin = PydanticInitPlugin()

    registry = PluginRegistry([cli_plugin, serialization_plugin, openapi_plugin, init_plugin])

    assert registry.openapi == (openapi_plugin,)
    assert registry.cli == (cli_plugin,)
    assert registry.serialization == (serialization_plugin,)
    assert registry.init == (init_plugin,)

    assert openapi_plugin in registry
    assert serialization_plugin in registry
    assert init_plugin in registry
    assert cli_plugin in registry

    assert set(registry) == {openapi_plugin, cli_plugin, init_plugin, serialization_plugin}


def test_plugin_registry_get() -> None:
    class CLIPlugin(CLIPluginProtocol):
        def on_cli_init(self, cli: Group) -> None:
            pass

    cli_plugin = CLIPlugin()

    with pytest.raises(KeyError, match="No plugin of type 'CLIPlugin' registered"):
        PluginRegistry([]).get(CLIPlugin)

    assert PluginRegistry([cli_plugin]).get(CLIPlugin) is cli_plugin


def test_plugin_registry_stringified_get() -> None:
    class CLIPlugin(CLIPluginProtocol):
        def on_cli_init(self, cli: Group) -> None:
            pass

    cli_plugin = CLIPlugin()
    pydantic_plugin = PydanticPlugin()
    with pytest.raises(KeyError):
        PluginRegistry([CLIPlugin()]).get(
            "litestar2.contrib.pydantic.PydanticPlugin"
        )  # not a fqdn.  should fail # type: ignore[list-item]
        PluginRegistry([]).get("CLIPlugin")  # not a fqdn.  should fail # type: ignore[list-item]

    assert PluginRegistry([cli_plugin, pydantic_plugin]).get(CLIPlugin) is cli_plugin
    assert PluginRegistry([cli_plugin, pydantic_plugin]).get(PydanticPlugin) is pydantic_plugin
    assert PluginRegistry([cli_plugin, pydantic_plugin]).get("PydanticPlugin") is pydantic_plugin
    assert (
        PluginRegistry([cli_plugin, pydantic_plugin]).get("litestar.contrib.pydantic.PydanticPlugin") is pydantic_plugin
    )


def test_openapi_schema_plugin_is_constrained_field() -> None:
    assert OpenAPISchemaPlugin.is_constrained_field(FieldDefinition.from_annotation(str)) is False


def test_openapi_schema_plugin_is_undefined_sentinel() -> None:
    for value in UNDEFINED_SENTINELS:
        assert OpenAPISchemaPlugin.is_undefined_sentinel(value) is False


@pytest.mark.parametrize(("init_plugin",), [(PydanticInitPlugin(),), (None,)])
@pytest.mark.parametrize(("schema_plugin",), [(PydanticSchemaPlugin(),), (None,)])
@pytest.mark.parametrize(("attrs_plugin",), [(AttrsSchemaPlugin(),), (None,)])
def test_app_get_default_plugins(
    init_plugin: PydanticInitPlugin, schema_plugin: PydanticSchemaPlugin, attrs_plugin: AttrsSchemaPlugin
) -> None:
    plugins = [p for p in (init_plugin, schema_plugin, attrs_plugin) if p is not None]
    any_pydantic = bool(init_plugin) or bool(schema_plugin)
    default_plugins = Litestar._get_default_plugins(plugins)  # type: ignore[arg-type]
    if not any_pydantic:
        assert {type(p) for p in default_plugins} == {
            PydanticPlugin,
            AttrsSchemaPlugin,
            PydanticDIPlugin,
            MsgspecDIPlugin,
        }
    else:
        assert {type(p) for p in default_plugins} == {
            PydanticInitPlugin,
            PydanticSchemaPlugin,
            AttrsSchemaPlugin,
            PydanticDIPlugin,
            MsgspecDIPlugin,
        }
