from __future__ import annotations

import uuid
from datetime import date
from uuid import UUID

from sqlalchemy import ForeignKey, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from litestar import Litestar, get
from litestar.plugins.sqlalchemy import AsyncSessionConfig, SQLAlchemyAsyncConfig, SQLAlchemyPlugin, base


# The SQLAlchemy base includes a declarative model for you to use in your models.
# The `UUIDBase` class includes a `UUID` based primary key (`id`)
class Author(base.UUIDBase):
    __tablename__ = "author"
    name: Mapped[str]
    dob: Mapped[date]
    books: Mapped[list[Book]] = relationship(back_populates="author", lazy="selectin")


# The `UUIDAuditBase` class includes the same UUID` based primary key (`id`) and 2
# additional columns: `created_at` and `updated_at`. `created_at` is a timestamp of when the
# record created, and `updated_at` is the last time the record was modified.
class Book(base.UUIDAuditBase):
    __tablename__ = "book"
    title: Mapped[str]
    author_id: Mapped[UUID] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(lazy="joined", innerjoin=True, viewonly=True)


session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///test.sqlite", session_config=session_config, create_all=True
)  # Create 'async_session' dependency.


async def on_startup(app: Litestar) -> None:
    """Adds some dummy data if no data is present."""
    async with sqlalchemy_config.get_session() as session:
        statement = select(func.count()).select_from(Author)
        count = await session.execute(statement)
        if not count.scalar():
            author_id = uuid.uuid4()
            session.add(Author(name="Stephen King", dob=date(1954, 9, 21), id=author_id))
            session.add(Book(title="It", author_id=author_id))
            await session.commit()


@get(path="/authors")
async def get_authors(db_session: AsyncSession, db_engine: AsyncEngine) -> list[Author]:
    """Interact with SQLAlchemy engine and session."""
    return list(await db_session.scalars(select(Author)))


app = Litestar(
    route_handlers=[get_authors],
    on_startup=[on_startup],
    debug=True,
    plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
)
