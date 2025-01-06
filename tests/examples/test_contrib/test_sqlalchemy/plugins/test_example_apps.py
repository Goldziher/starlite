from __future__ import annotations

from typing import Any, AsyncIterator, Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch
from sqlalchemy import Engine, StaticPool, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from litestar.plugins.sqlalchemy import EngineConfig
from litestar.testing import TestClient

pytestmark = pytest.mark.xdist_group("sqlalchemy_examples")


@pytest.fixture
def data() -> list[dict[str, Any]]:
    return [{"title": "test", "done": False}]


@pytest.fixture()
def sqlite_engine() -> Generator[None, Engine]:
    yield create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


@pytest.fixture()
async def aiosqlite_engine() -> AsyncIterator[AsyncEngine]:
    yield create_async_engine("sqlite+aiosqlite://", connect_args={"check_same_thread": False})


@pytest.mark.anyio
async def test_sqlalchemy_async_plugin_example(
    data: dict[str, Any], monkeypatch: MonkeyPatch, aiosqlite_engine: AsyncEngine
) -> None:
    from docs.examples.contrib.sqlalchemy.plugins import sqlalchemy_async_plugin_example

    monkeypatch.setattr(sqlalchemy_async_plugin_example.config, "engine_instance", aiosqlite_engine)

    with TestClient(sqlalchemy_async_plugin_example.app) as client:
        assert client.post("/", json=data[0]).json() == data


def test_sqlalchemy_sync_plugin_example(data: dict[str, Any], monkeypatch: MonkeyPatch, sqlite_engine: Engine) -> None:
    from docs.examples.contrib.sqlalchemy.plugins import sqlalchemy_sync_plugin_example

    monkeypatch.setattr(sqlalchemy_sync_plugin_example.config, "engine_instance", sqlite_engine)

    with TestClient(sqlalchemy_sync_plugin_example.app) as client:
        assert client.post("/", json=data[0]).json() == data


@pytest.mark.anyio
async def test_sqlalchemy_async_init_plugin_example(
    data: dict[str, Any], monkeypatch: MonkeyPatch, aiosqlite_engine: AsyncEngine
) -> None:
    from docs.examples.contrib.sqlalchemy.plugins import sqlalchemy_async_init_plugin_example

    monkeypatch.setattr(sqlalchemy_async_init_plugin_example.config, "engine_instance", aiosqlite_engine)

    with TestClient(sqlalchemy_async_init_plugin_example.app) as client:
        assert client.post("/", json=data[0]).json() == data


@pytest.mark.anyio
async def test_sqlalchemy_sync_init_plugin_example(
    data: dict[str, Any], monkeypatch: MonkeyPatch, sqlite_engine: Engine
) -> None:
    from docs.examples.contrib.sqlalchemy.plugins import sqlalchemy_sync_init_plugin_example

    monkeypatch.setattr(sqlalchemy_sync_init_plugin_example.config, "engine_instance", sqlite_engine)

    with TestClient(sqlalchemy_sync_init_plugin_example.app) as client:
        assert client.post("/", json=data[0]).json() == data


@pytest.mark.anyio
async def test_sqlalchemy_async_init_plugin_dependencies(
    monkeypatch: MonkeyPatch, aiosqlite_engine: AsyncEngine
) -> None:
    from docs.examples.contrib.sqlalchemy.plugins import sqlalchemy_async_dependencies

    monkeypatch.setattr(sqlalchemy_async_dependencies.config, "engine_instance", aiosqlite_engine)
    with TestClient(sqlalchemy_async_dependencies.app) as client:
        assert client.post("/").json() == [1, 2]


def test_sqlalchemy_sync_init_plugin_dependencies(monkeypatch: MonkeyPatch) -> None:
    from docs.examples.contrib.sqlalchemy.plugins import sqlalchemy_sync_dependencies

    engine_config = EngineConfig(connect_args={"check_same_thread": False}, poolclass=StaticPool)
    monkeypatch.setattr(sqlalchemy_sync_dependencies.config, "connection_string", "sqlite://")
    monkeypatch.setattr(sqlalchemy_sync_dependencies.config, "engine_config", engine_config)
    with TestClient(sqlalchemy_sync_dependencies.app) as client:
        assert client.post("/").json() == [1, 2]


def test_sqlalchemy_async_before_send_handler() -> None:
    from docs.examples.contrib.sqlalchemy.plugins.sqlalchemy_async_before_send_handler import app

    from litestar.plugins.sqlalchemy import async_autocommit_before_send_handler

    assert async_autocommit_before_send_handler is app.before_send[0]


def test_sqlalchemy_sync_before_send_handler() -> None:
    from docs.examples.contrib.sqlalchemy.plugins.sqlalchemy_sync_before_send_handler import app

    from litestar.plugins.sqlalchemy import sync_autocommit_before_send_handler

    assert sync_autocommit_before_send_handler is app.before_send[0].func


def test_sqlalchemy_async_serialization_plugin(data: dict[str, Any]) -> None:
    from docs.examples.contrib.sqlalchemy.plugins.sqlalchemy_async_serialization_plugin import app

    with TestClient(app) as client:
        assert client.post("/", json=data[0]).json() == data


def test_sqlalchemy_sync_serialization_plugin(data: dict[str, Any]) -> None:
    from docs.examples.contrib.sqlalchemy.plugins.sqlalchemy_sync_serialization_plugin import app

    with TestClient(app) as client:
        assert client.post("/", json=data[0]).json() == data


def test_sqlalchemy_async_serialization_dto(data: dict[str, Any]) -> None:
    from docs.examples.contrib.sqlalchemy.plugins.sqlalchemy_async_serialization_dto import app

    with TestClient(app) as client:
        assert client.post("/", json=data[0]).json() == data


def test_sqlalchemy_async_serialization_plugin_marking_fields(data: dict[str, Any]) -> None:
    from docs.examples.contrib.sqlalchemy.plugins.sqlalchemy_async_serialization_plugin_marking_fields import app

    with TestClient(app) as client:
        assert client.post("/", json=data[0]).json() == data


def test_sqlalchemy_sync_serialization_plugin_marking_fields(data: dict[str, Any]) -> None:
    from docs.examples.contrib.sqlalchemy.plugins.sqlalchemy_sync_serialization_plugin_marking_fields import app

    with TestClient(app) as client:
        assert client.post("/", json=data[0]).json() == data
