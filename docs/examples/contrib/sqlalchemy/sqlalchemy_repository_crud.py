from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, datetime
from uuid import UUID

import anyio
from rich import get_console
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped

from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository

console = get_console()


# the SQLAlchemy base includes a declarative model for you to use in your models.
# The `Base` class includes a `UUID` based primary key (`id`)
class Author(UUIDBase):
    name: Mapped[str]
    dob: Mapped[date]
    dod: Mapped[date | None]


class AuthorRepository(SQLAlchemyAsyncRepository[Author]):
    """Author repository."""

    model_type = Author


engine = create_async_engine(
    "sqlite+aiosqlite:///test.sqlite",
    future=True,
)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


# let's make a simple context manager as an example here.
@asynccontextmanager
async def repository_factory() -> AsyncIterator[AuthorRepository]:
    async with session_factory() as db_session:
        try:
            yield AuthorRepository(session=db_session)
        except Exception:  # noqa: BLE001
            await db_session.rollback()
        else:
            await db_session.commit()


async def create_author() -> Author:
    async with repository_factory() as repo:
        obj = await repo.add(
            Author(
                name="F. Scott Fitzgerald",
                dob=datetime.strptime("1896-09-24", "%Y-%m-%d").date(),
            )
        )
        console.print(f"Created Author record for {obj.name} with primary key {obj.id}.")
        return obj


async def update_author(obj: Author) -> Author:
    async with repository_factory() as repo:
        obj = await repo.update(obj)
        console.print(f"Updated Author record for {obj.name} with primary key {obj.id}.")
        return obj


async def remove_author(id: UUID) -> Author:
    async with repository_factory() as repo:
        obj = await repo.delete(id)
        console.print(f"Deleted Author record for {obj.name} with primary key {obj.id}.")
        return obj


async def get_author_if_exists(id: UUID) -> Author | None:
    async with repository_factory() as repo:
        obj = await repo.get_one_or_none(id=id)
        if obj is not None:
            console.print(f"Found Author record for {obj.name} with primary key {obj.id}.")
        else:
            console.print(f"Could not find Author with primary key {id}.")
        return obj


async def run_script() -> None:
    """Load data from a fixture."""
    async with engine.begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)

    # 1) create a new Author record.
    console.print("1) Adding a new record")
    author = await create_author()
    author_id = author.id

    # 2) Let's update the Author record.
    console.print("2) Updating a record.")
    author.dod = datetime.strptime("1940-12-21", "%Y-%m-%d").date()
    await update_author(author)

    # 3) Let's delete the record we just created.
    console.print("3) Removing a record.")
    await remove_author(author_id)

    # 4) Let's verify the record no longer exists.
    console.print("4) Select one or none.")
    _should_be_none = await get_author_if_exists(author_id)


if __name__ == "__main__":
    anyio.run(run_script)
