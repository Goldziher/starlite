from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine

from litestar import Litestar


@asynccontextmanager
async def db_connection(app: Litestar) -> AsyncGenerator[None, None]:
    engine = getattr(app.state, "engine", None)
    if engine is None:
        engine = create_async_engine("postgresql+asyncpg://postgres:mysecretpassword@pg.db:5432/db")
        app.state.engine = engine

    try:
        yield
    finally:
        await engine.dispose()


app = Litestar(lifespan=[db_connection])
