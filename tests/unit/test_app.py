# ruff: noqa: UP006
from __future__ import annotations

import inspect
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import fields
from typing import TYPE_CHECKING, Callable, List, Tuple
from unittest.mock import MagicMock, Mock, PropertyMock

import pytest
from click import Group
from pytest import MonkeyPatch

from litestar import Litestar, MediaType, Request, Response, get
from litestar.config.app import AppConfig
from litestar.config.response_cache import ResponseCacheConfig
from litestar.contrib.sqlalchemy.plugins import SQLAlchemySerializationPlugin
from litestar.datastructures import MutableScopeHeaders, State
from litestar.events.emitter import SimpleEventEmitter
from litestar.exceptions import (
    ImproperlyConfiguredException,
    InternalServerException,
    LitestarWarning,
    NotFoundException,
)
from litestar.logging.config import LoggingConfig
from litestar.plugins import CLIPluginProtocol
from litestar.router import Router
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.testing import TestClient, create_test_client

if TYPE_CHECKING:
    from typing import Dict

    from litestar.types import Message, Scope


@pytest.fixture()
def app_config_object() -> AppConfig:
    return AppConfig(
        after_exception=[],
        after_request=None,
        after_response=None,
        allowed_hosts=[],
        before_request=None,
        before_send=[],
        response_cache_config=ResponseCacheConfig(),
        cache_control=None,
        compression_config=None,
        cors_config=None,
        csrf_config=None,
        debug=False,
        dependencies={},
        etag=None,
        event_emitter_backend=SimpleEventEmitter,
        exception_handlers={},
        guards=[],
        listeners=[],
        logging_config=None,
        middleware=[],
        multipart_form_part_limit=1000,
        on_shutdown=[],
        on_startup=[],
        openapi_config=None,
        opt={},
        parameters={},
        plugins=[],
        request_class=None,
        response_class=None,
        response_cookies=[],
        response_headers=[],
        route_handlers=[],
        security=[],
        static_files_config=[],
        tags=[],
        template_config=None,
        websocket_class=None,
    )


def test_access_openapi_schema_raises_if_not_configured() -> None:
    """Test that accessing the openapi schema raises if not configured."""
    app = Litestar(openapi_config=None)
    with pytest.raises(ImproperlyConfiguredException):
        app.openapi_schema


def test_set_debug_updates_logging_level() -> None:
    app = Litestar()

    assert app.logger is not None
    assert app.logger.level == logging.INFO  # type: ignore[attr-defined]

    app.debug = True
    assert app.logger.level == logging.DEBUG  # type: ignore[attr-defined]

    app.debug = False
    assert app.logger.level == logging.INFO  # type: ignore[attr-defined]


@pytest.mark.parametrize("env_name,app_attr", [("LITESTAR_DEBUG", "debug"), ("LITESTAR_PDB", "pdb_on_exception")])
@pytest.mark.parametrize(
    "env_value,app_value,expected_value",
    [
        (None, None, False),
        (None, False, False),
        (None, True, True),
        ("0", None, False),
        ("0", False, False),
        ("0", True, True),
        ("1", None, True),
        ("1", False, False),
        ("1", True, True),
    ],
)
@pytest.mark.filterwarnings("ignore::litestar.utils.warnings.LitestarWarning:")
def test_set_env_flags(
    monkeypatch: MonkeyPatch,
    env_value: str | None,
    app_value: bool | None,
    expected_value: bool,
    env_name: str,
    app_attr: str,
) -> None:
    if env_value is not None:
        monkeypatch.setenv(env_name, env_value)
    else:
        monkeypatch.delenv(env_name, raising=False)

    app = Litestar(**{app_attr: app_value})  # type: ignore[arg-type]

    assert getattr(app, app_attr) is expected_value


def test_warn_pdb_on_exception() -> None:
    with pytest.warns(LitestarWarning, match="Debugger"):
        Litestar(pdb_on_exception=True)


def test_app_params_defined_on_app_config_object() -> None:
    """Ensures that all parameters to the `Litestar` constructor are present on the `AppConfig` object."""
    litestar_signature = inspect.signature(Litestar)
    app_config_fields = {f.name for f in fields(AppConfig)}
    for name in litestar_signature.parameters:
        if name in {"on_app_init", "initial_state", "_preferred_validation_backend"}:
            continue
        assert name in app_config_fields
    # ensure there are not fields defined on AppConfig that aren't in the Litestar signature
    assert not (app_config_fields - set(litestar_signature.parameters.keys()))


def test_app_config_object_used(app_config_object: AppConfig, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure that the properties on the `AppConfig` object are accessed within the `Litestar` constructor.

    In the test we replace every field on the `AppConfig` type with a property mock so that we can check that it has at
    least been accessed. It doesn't actually check that we do the right thing with it, but is a guard against the case
    of adding a parameter to the `Litestar` signature and to the `AppConfig` object, and using the value from the
    parameter downstream from construction of the `AppConfig` object.
    """

    # replace each field on the `AppConfig` object with a `PropertyMock`, this allows us to assert that the properties
    # have been accessed during app instantiation.
    property_mocks: List[Tuple[str, Mock]] = []
    for field in fields(AppConfig):
        property_mock = PropertyMock()
        property_mocks.append((field.name, property_mock))
        monkeypatch.setattr(type(app_config_object), field.name, property_mock, raising=False)

    # Things that we don't actually need to call for this test
    monkeypatch.setattr(Litestar, "register", MagicMock())
    monkeypatch.setattr(Litestar, "_create_asgi_handler", MagicMock())
    monkeypatch.setattr(Router, "__init__", MagicMock())

    # instantiates the app with an `on_app_config` that returns our patched `AppConfig` object.
    Litestar(on_app_init=[MagicMock(return_value=app_config_object)])

    # this ensures that each of the properties of the `AppConfig` object have been accessed within `Litestar.__init__()`
    for name, mock in property_mocks:
        assert mock.called, f"expected {name} to be called"


def test_app_debug_create_logger() -> None:
    app = Litestar([], debug=True)

    assert app.logging_config
    assert app.logging_config.loggers["litestar"]["level"] == "DEBUG"  # type: ignore[attr-defined]


def test_app_debug_explicitly_disable_logging() -> None:
    app = Litestar([], logging_config=None)

    assert not app.logging_config


def test_app_debug_update_logging_config() -> None:
    logging_config = LoggingConfig()
    app = Litestar([], logging_config=logging_config, debug=True)

    assert app.logging_config is logging_config
    assert app.logging_config.loggers["litestar"]["level"] == "DEBUG"  # type: ignore[attr-defined]


def test_set_state() -> None:
    def modify_state_in_hook(app_config: AppConfig) -> AppConfig:
        assert isinstance(app_config.state, State)
        app_config.state["c"] = "D"
        app_config.state["e"] = "f"
        return app_config

    app = Litestar(state=State({"a": "b", "c": "d"}), on_app_init=[modify_state_in_hook])
    assert app.state._state == {"a": "b", "c": "D", "e": "f"}


async def test_dont_override_initial_state(create_scope: Callable[..., Scope]) -> None:
    app = Litestar()

    scope = create_scope(headers=[], state={"foo": "bar"})

    async def send(message: Message) -> None:
        pass

    async def receive() -> None:
        pass

    await app(scope, receive, send)  # type: ignore[arg-type]

    assert scope["state"].get("foo") == "bar"


def test_app_from_config(app_config_object: AppConfig) -> None:
    Litestar.from_config(app_config_object)


def test_before_send() -> None:
    @get("/test")
    def handler() -> Dict[str, str]:
        return {"key": "value"}

    async def before_send_hook_handler(message: Message, scope: Scope) -> None:
        if message["type"] == "http.response.start":
            headers = MutableScopeHeaders(message)
            headers.add("My Header", scope["app"].state.message)

    def on_startup(app: Litestar) -> None:
        app.state.message = "value injected during send"

    with create_test_client(handler, on_startup=[on_startup], before_send=[before_send_hook_handler]) as client:
        response = client.get("/test")
        assert response.status_code == HTTP_200_OK
        assert response.headers.get("My Header") == "value injected during send"


def test_using_custom_http_exception_handler() -> None:
    @get("/{param:int}")
    def my_route_handler(param: int) -> None:
        ...

    def my_custom_handler(_: Request, __: Exception) -> Response:
        return Response(content="custom message", media_type=MediaType.TEXT, status_code=HTTP_400_BAD_REQUEST)

    with create_test_client(my_route_handler, exception_handlers={NotFoundException: my_custom_handler}) as client:
        response = client.get("/abc")
        assert response.text == "custom message"
        assert response.status_code == HTTP_400_BAD_REQUEST


def test_debug_response_created() -> None:
    # this will test exception causes are recorded in output
    # since frames include code in context we should not raise
    # exception directly
    def exception_thrower() -> float:
        return 1 / 0

    @get("/")
    def my_route_handler() -> None:
        try:
            exception_thrower()
        except Exception as e:
            raise InternalServerException() from e

    app = Litestar(route_handlers=[my_route_handler], debug=True)
    client = TestClient(app=app)

    response = client.get("/")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    assert "text/plain" in response.headers["content-type"]

    response = client.get("/", headers={"accept": "text/html"})
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    assert "text/html" in response.headers["content-type"]
    assert "ZeroDivisionError" in response.text


def test_handler_error_return_status_500() -> None:
    @get("/")
    def my_route_handler() -> None:
        raise KeyError("custom message")

    with create_test_client(my_route_handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_lifespan() -> None:
    events: list[str] = []
    counter = {"value": 0}

    def sync_function_without_app() -> None:
        events.append("sync_function_without_app")
        counter["value"] += 1

    async def async_function_without_app() -> None:
        events.append("async_function_without_app")
        counter["value"] += 1

    def sync_function_with_app(app: Litestar) -> None:
        events.append("sync_function_with_app")
        assert app is not None
        assert isinstance(app.state, State)
        counter["value"] += 1
        app.state.x = True

    async def async_function_with_app(app: Litestar) -> None:
        events.append("async_function_with_app")
        assert app is not None
        assert isinstance(app.state, State)
        counter["value"] += 1
        app.state.y = True

    with create_test_client(
        [],
        on_startup=[
            sync_function_without_app,
            async_function_without_app,
            sync_function_with_app,
            async_function_with_app,
        ],
        on_shutdown=[
            sync_function_without_app,
            async_function_without_app,
            sync_function_with_app,
            async_function_with_app,
        ],
    ) as client:
        assert counter["value"] == 4
        assert client.app.state.x
        assert client.app.state.y
        counter["value"] = 0
        assert counter["value"] == 0
    assert counter["value"] == 4
    assert events == [
        "sync_function_without_app",
        "async_function_without_app",
        "sync_function_with_app",
        "async_function_with_app",
        "sync_function_without_app",
        "async_function_without_app",
        "sync_function_with_app",
        "async_function_with_app",
    ]


def test_registering_route_handler_generates_openapi_docs() -> None:
    def fn() -> None:
        return

    app = Litestar(route_handlers=[])
    assert app.openapi_schema

    app.register(get("/path1")(fn))

    assert app.openapi_schema.paths is not None
    assert app.openapi_schema.paths.get("/path1")

    app.register(get("/path2")(fn))
    assert app.openapi_schema.paths.get("/path1")
    assert app.openapi_schema.paths.get("/path2")


def test_plugin_properties() -> None:
    class FooPlugin(CLIPluginProtocol):
        def on_cli_init(self, cli: Group) -> None:
            return

    app = Litestar(plugins=[FooPlugin(), SQLAlchemySerializationPlugin()])

    assert app.openapi_schema_plugins == list(app.plugins.openapi)
    assert app.cli_plugins == list(app.plugins.cli)
    assert app.serialization_plugins == list(app.plugins.serialization)


def test_plugin_registry() -> None:
    class FooPlugin(CLIPluginProtocol):
        def on_cli_init(self, cli: Group) -> None:
            return

    foo = FooPlugin()

    app = Litestar(plugins=[foo])

    assert foo in app.plugins.cli


def test_lifespan_context_and_shutdown_hook_execution_order() -> None:
    events: list[str] = []
    counter = {"value": 0}

    @asynccontextmanager
    async def lifespan_context_1(app: Litestar) -> AsyncGenerator[None, None]:
        try:
            yield
        finally:
            events.append("ctx_1")
            counter["value"] += 1

    @asynccontextmanager
    async def lifespan_context_2(app: Litestar) -> AsyncGenerator[None, None]:
        try:
            yield
        finally:
            events.append("ctx_2")
            counter["value"] += 1

    async def hook_a(app: Litestar) -> None:
        events.append("hook_a")
        counter["value"] += 1

    async def hook_b(app: Litestar) -> None:
        events.append("hook_b")
        counter["value"] += 1

    with create_test_client(
        route_handlers=[],
        lifespan=[
            lifespan_context_1,
            lifespan_context_2,
        ],
        on_shutdown=[hook_a, hook_b],
    ):
        assert counter["value"] == 0

    assert counter["value"] == 4
    assert events[0] == "ctx_2"
    assert events[1] == "ctx_1"
    assert events[2] == "hook_a"
    assert events[3] == "hook_b"
