from __future__ import annotations

from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from litestar.testing import TestClient


@pytest.fixture(autouse=True)
async def _clean_db() -> AsyncGenerator[None, None]:
    from docs.examples.contrib.sqlalchemy.plugins.tutorial.full_app_no_plugins import Base

    engine = create_async_engine("sqlite+aiosqlite:///todo.sqlite")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_no_plugins_full_app() -> None:
    from docs.examples.contrib.sqlalchemy.plugins.tutorial.full_app_no_plugins import (
        app,
    )

    TODO = {"title": "Start writing TODO list", "done": True}
    TODO_LIST = [TODO]

    with TestClient(app) as client:
        response = client.post("/", json=TODO)
        assert response.status_code == 201
        assert response.json() == TODO

        response = client.post("/", json=TODO)
        assert response.status_code == 409

        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == TODO_LIST

        response = client.get("/?done=false")
        assert response.status_code == 200
        assert response.json() == []

        response = client.put("/Start writing another list", json=TODO)
        assert response.status_code == 404

        updated_todo = dict(TODO)
        updated_todo["done"] = False
        response = client.put("/Start writing TODO list", json=updated_todo)
        assert response.status_code == 200
        assert response.json() == updated_todo
