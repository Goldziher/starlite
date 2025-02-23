from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from litestar import Litestar, post
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin

if TYPE_CHECKING:
    from typing import Any

    from sqlalchemy.ext.asyncio import AsyncSession


class Base(DeclarativeBase): ...


class TodoItem(Base):
    __tablename__ = "todo_item"
    title: Mapped[str] = mapped_column(primary_key=True)
    done: Mapped[bool]


@post("/")
async def add_item(data: dict[str, Any], db_session: AsyncSession) -> list[dict[str, Any]]:
    todo_item = TodoItem(**data)
    async with db_session.begin():
        db_session.add(todo_item)
    return [
        {
            "title": item.title,
            "done": item.done,
        }
        for item in (await db_session.execute(select(TodoItem))).scalars()
    ]


async def init_db(app: Litestar) -> None:
    async with config.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


config = SQLAlchemyAsyncConfig(connection_string="sqlite+aiosqlite:///todo_async.sqlite")
plugin = SQLAlchemyInitPlugin(config=config)
app = Litestar(route_handlers=[add_item], plugins=[plugin], on_startup=[init_db], debug=True)
