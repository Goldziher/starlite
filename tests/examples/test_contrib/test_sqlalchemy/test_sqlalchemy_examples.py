from pathlib import Path

import pytest
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from litestar.plugins.sqlalchemy import AsyncSessionConfig, SQLAlchemyAsyncConfig
from litestar.testing import TestClient

pytestmark = pytest.mark.xdist_group("sqlalchemy_examples")


@pytest.mark.anyio
async def test_sqlalchemy_declarative_models(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///test.sqlite", poolclass=NullPool)

    session_config = AsyncSessionConfig(expire_on_commit=False)
    sqlalchemy_config = SQLAlchemyAsyncConfig(
        session_config=session_config,
        create_all=True,
        engine_instance=engine,
    )  # Create 'async_session' dependency.
    from docs.examples.contrib.sqlalchemy import sqlalchemy_declarative_models

    monkeypatch.setattr(sqlalchemy_declarative_models, "sqlalchemy_config", sqlalchemy_config)
    async with engine.begin() as connection:
        await connection.run_sync(sqlalchemy_declarative_models.Author.metadata.create_all)
        await connection.commit()
    with TestClient(sqlalchemy_declarative_models.app) as client:
        response = client.get("/authors")
        assert response.status_code == 200
        assert len(response.json()) > 0
