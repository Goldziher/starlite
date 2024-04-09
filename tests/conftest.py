from __future__ import annotations

import importlib.util
import logging
import os
import random
import string
import sys
from datetime import datetime
from os import urandom
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Generator, TypeVar, Union, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_lazy_fixtures import lf
from redis.asyncio import Redis as AsyncRedis
from redis.client import Redis
from time_machine import travel

from litestar.logging import LoggingConfig
from litestar.logging.config import default_handlers as logging_default_handlers
from litestar.middleware.session import SessionMiddleware
from litestar.middleware.session.base import BaseSessionBackend
from litestar.middleware.session.client_side import ClientSideSessionBackend, CookieBackendConfig
from litestar.middleware.session.server_side import ServerSideSessionBackend, ServerSideSessionConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.stores.base import Store
from litestar.stores.file import FileStore
from litestar.stores.memory import MemoryStore
from litestar.stores.redis import RedisStore
from litestar.testing import RequestFactory

if TYPE_CHECKING:
    from types import ModuleType

    from pytest import FixtureRequest, MonkeyPatch
    from time_machine import Coordinates

    from litestar import Litestar
    from litestar.types import (
        AnyIOBackend,
        ASGIApp,
        ASGIVersion,
        GetLogger,
        Receive,
        RouteHandlerType,
        Scope,
        ScopeSession,
        Send,
    )


pytest_plugins = ["tests.docker_service_fixtures"]


@pytest.fixture
def mock() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def async_mock() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(params=[pytest.param("asyncio", id="asyncio"), pytest.param("trio", id="trio")])
def anyio_backend(request: pytest.FixtureRequest) -> str:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture()
def mock_asgi_app() -> ASGIApp:
    async def asgi_app(scope: Scope, receive: Receive, send: Send) -> None: ...

    return asgi_app


@pytest.fixture()
def redis_store(redis_client: AsyncRedis) -> RedisStore:
    return RedisStore(redis=redis_client)


@pytest.fixture()
def memory_store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture()
def file_store(tmp_path: Path) -> FileStore:
    return FileStore(path=tmp_path)


@pytest.fixture(
    params=[pytest.param("redis_store", marks=pytest.mark.xdist_group("redis")), "memory_store", "file_store"]
)
def store(request: FixtureRequest) -> Store:
    return cast("Store", request.getfixturevalue(request.param))


@pytest.fixture
def cookie_session_backend_config() -> CookieBackendConfig:
    return CookieBackendConfig(secret=urandom(16))


@pytest.fixture()
def cookie_session_backend(cookie_session_backend_config: CookieBackendConfig) -> ClientSideSessionBackend:
    return ClientSideSessionBackend(config=cookie_session_backend_config)


@pytest.fixture(
    params=[
        pytest.param(lf("cookie_session_backend_config"), id="cookie"),
        pytest.param(lf("server_side_session_config"), id="server-side"),
    ]
)
def session_backend_config(request: pytest.FixtureRequest) -> ServerSideSessionConfig | CookieBackendConfig:
    return cast("Union[ServerSideSessionConfig, CookieBackendConfig]", request.param)


@pytest.fixture()
def server_side_session_config() -> ServerSideSessionConfig:
    return ServerSideSessionConfig()


@pytest.fixture()
def server_side_session_backend(server_side_session_config: ServerSideSessionConfig) -> ServerSideSessionBackend:
    return ServerSideSessionBackend(config=server_side_session_config)


@pytest.fixture(
    params=[
        pytest.param("cookie_session_backend", id="cookie"),
        pytest.param("server_side_session_backend", id="server-side"),
    ]
)
def session_backend(request: pytest.FixtureRequest) -> BaseSessionBackend:
    return cast("BaseSessionBackend", request.getfixturevalue(request.param))


@pytest.fixture()
def session_backend_config_memory(memory_store: MemoryStore) -> ServerSideSessionConfig:
    return ServerSideSessionConfig()


@pytest.fixture
def session_middleware(session_backend: BaseSessionBackend, mock_asgi_app: ASGIApp) -> SessionMiddleware[Any]:
    return SessionMiddleware(app=mock_asgi_app, backend=session_backend)


@pytest.fixture
def cookie_session_middleware(
    cookie_session_backend: ClientSideSessionBackend, mock_asgi_app: ASGIApp
) -> SessionMiddleware[ClientSideSessionBackend]:
    return SessionMiddleware(app=mock_asgi_app, backend=cookie_session_backend)


@pytest.fixture
def test_client_backend(anyio_backend_name: str) -> AnyIOBackend:
    return cast("AnyIOBackend", anyio_backend_name)


@pytest.fixture
def create_scope() -> Callable[..., Scope]:
    def inner(
        *,
        type: str = "http",
        app: Litestar | None = None,
        asgi: ASGIVersion | None = None,
        auth: Any = None,
        client: tuple[str, int] | None = ("testclient", 50000),
        extensions: dict[str, dict[object, object]] | None = None,
        http_version: str = "1.1",
        path: str = "/",
        path_params: dict[str, str] | None = None,
        query_string: str = "",
        root_path: str = "",
        route_handler: RouteHandlerType | None = None,
        scheme: str = "http",
        server: tuple[str, int | None] | None = ("testserver", 80),
        session: ScopeSession | None = None,
        state: dict[str, Any] | None = None,
        user: Any = None,
        **kwargs: dict[str, Any],
    ) -> Scope:
        scope = {
            "app": app,
            "asgi": asgi or {"spec_version": "2.0", "version": "3.0"},
            "auth": auth,
            "type": type,
            "path": path,
            "raw_path": path.encode(),
            "root_path": root_path,
            "scheme": scheme,
            "query_string": query_string.encode(),
            "client": client,
            "server": server,
            "method": "GET",
            "http_version": http_version,
            "extensions": extensions or {"http.response.template": {}},
            "state": state or {},
            "path_params": path_params or {},
            "route_handler": route_handler,
            "user": user,
            "session": session,
            **kwargs,
        }
        return cast("Scope", scope)

    return inner


@pytest.fixture
def scope(create_scope: Callable[..., Scope]) -> Scope:
    return create_scope()


@pytest.fixture
def create_module(tmp_path: Path, monkeypatch: MonkeyPatch) -> Callable[[str], ModuleType]:
    """Utility fixture for dynamic module creation."""

    def wrapped(source: str) -> ModuleType:
        """

        Args:
            source: Source code as a string.

        Returns:
            An imported module.
        """
        T = TypeVar("T")

        def not_none(val: T | T | None) -> T:
            assert val is not None
            return val

        def module_name_generator() -> str:
            letters = string.ascii_lowercase
            return "".join(random.choice(letters) for _ in range(10))

        module_name = module_name_generator()
        path = tmp_path / f"{module_name}.py"
        path.write_text(source)
        # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
        spec = not_none(importlib.util.spec_from_file_location(module_name, path))
        module = not_none(importlib.util.module_from_spec(spec))
        monkeypatch.setitem(sys.modules, module_name, module)
        not_none(spec.loader).exec_module(module)
        return module

    return wrapped


@pytest.fixture()
def frozen_datetime() -> Generator[Coordinates, None, None]:
    with travel(datetime.utcnow, tick=False) as frozen:
        yield frozen


@pytest.fixture()
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture()
def reset_httpx_logging() -> Generator[None, None, None]:
    # ensure that httpx logging is not interfering with our test client
    httpx_logger = logging.getLogger("httpx")
    initial_level = httpx_logger.level
    httpx_logger.setLevel(logging.WARNING)
    yield
    httpx_logger.setLevel(initial_level)


# the monkeypatch fixture does not work with session scoped dependencies
@pytest.fixture(autouse=True, scope="session")
def disable_warn_implicit_sync_to_thread() -> Generator[None, None, None]:
    old_value = os.getenv("LITESTAR_WARN_IMPLICIT_SYNC_TO_THREAD")
    os.environ["LITESTAR_WARN_IMPLICIT_SYNC_TO_THREAD"] = "0"
    yield
    if old_value is not None:
        os.environ["LITESTAR_WARN_IMPLICIT_SYNC_TO_THREAD"] = old_value


@pytest.fixture()
def disable_warn_sync_to_thread_with_async(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("LITESTAR_WARN_SYNC_TO_THREAD_WITH_ASYNC", "0")


@pytest.fixture()
def enable_warn_implicit_sync_to_thread(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("LITESTAR_WARN_IMPLICIT_SYNC_TO_THREAD", "1")


@pytest.fixture
def get_logger() -> GetLogger:
    # due to the limitations of caplog we have to place this call here.
    # we also have to allow propagation.
    return LoggingConfig(
        handlers=logging_default_handlers,
        loggers={
            "litestar": {"level": "INFO", "handlers": ["queue_listener"], "propagate": True},
        },
    ).configure()


@pytest.fixture()
async def redis_client(docker_ip: str, redis_service: None) -> AsyncGenerator[AsyncRedis, None]:
    # this is to get around some weirdness with pytest-asyncio and redis interaction
    # on 3.8 and 3.9

    Redis(host=docker_ip, port=6397).flushall()
    client: AsyncRedis = AsyncRedis(host=docker_ip, port=6397)
    yield client
    try:
        await client.aclose()  # type: ignore[attr-defined]
    except RuntimeError:
        pass


@pytest.fixture(autouse=True)
def _patch_openapi_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("litestar.app.DEFAULT_OPENAPI_CONFIG", OpenAPIConfig(title="Litestar API", version="1.0.0"))
