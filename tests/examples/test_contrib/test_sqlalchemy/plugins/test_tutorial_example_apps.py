from __future__ import annotations

import importlib
import sys

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.monkeypatch import MonkeyPatch
from docs.examples.contrib.sqlalchemy.plugins.tutorial import (
    full_app_no_plugins,
    full_app_with_init_plugin,
    full_app_with_plugin,
    full_app_with_serialization_plugin,
    full_app_with_session_di,
)
from sqlalchemy.ext.asyncio import create_async_engine

from litestar import Litestar
from litestar.testing import TestClient

pytestmark = pytest.mark.xdist_group("sqlalchemy_examples")


@pytest.fixture(
    params=[
        full_app_no_plugins,
        full_app_with_init_plugin,
        full_app_with_plugin,
        full_app_with_serialization_plugin,
        full_app_with_session_di,
    ]
)
async def app(monkeypatch: MonkeyPatch, request: FixtureRequest) -> Litestar:
    app_module = importlib.reload(request.param)

    engine = create_async_engine("sqlite+aiosqlite://", connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(app_module.Base.metadata.create_all)

    try:
        monkeypatch.setattr(app_module, "create_async_engine", lambda *a, **kw: engine)
    except AttributeError:
        app_module.db_config.connection_string = None
        app_module.db_config.engine_instance = engine

    yield app_module.app
    await engine.dispose()


@pytest.mark.anyio
@pytest.mark.skipif(sys.platform != "linux", reason="Unknown - fails on Windows and macOS, in CI only")
async def test_no_plugins_full_app(app: Litestar) -> None:
    todo = {"title": "Start writing todo list", "done": True}
    todo_list = [todo]

    with TestClient(app) as client:
        response = client.post("/", json=todo)
        assert response.status_code == 201
        assert response.json() == todo

        response = client.post("/", json=todo)
        assert response.status_code == 409

        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == todo_list

        response = client.get("/?done=false")
        assert response.status_code == 200
        assert response.json() == []

        response = client.put("/Start writing another list", json=todo)
        assert response.status_code == 404

        updated_todo = dict(todo)
        updated_todo["done"] = False
        response = client.put("/Start writing todo list", json=updated_todo)
        assert response.status_code == 200
        assert response.json() == updated_todo
