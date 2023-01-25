from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, declarative_base

from starlite import AbstractAsyncOffsetPaginator, OffsetPagination, Provide, Starlite, get
from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin

Base = declarative_base()

if TYPE_CHECKING:
    from sqlalchemy.engine.result import ScalarResult


class Person(Base):
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String)


class PersonOffsetPaginator(AbstractAsyncOffsetPaginator[Person]):
    def __init__(self, async_session: AsyncSession) -> None:  # 'async_session' dependency will be injected here.
        self.async_session = async_session

    async def get_total(self) -> int:
        return await self.async_session.scalar(select(func.count(Person.id)))

    async def get_items(self, limit: int, offset: int) -> List[Person]:
        people: "ScalarResult" = await self.async_session.scalars(select(Person).slice(offset, limit))
        return list(people.all())


# Create a route handler. The handler will receive two query parameters - 'limit' and 'offset', which is passed
# to the paginator instance. Also create a dependency 'paginator' which will be injected into the handler.
@get("/people", dependencies={"paginator": Provide(PersonOffsetPaginator)})
async def people_handler(paginator: PersonOffsetPaginator, limit: int, offset: int) -> OffsetPagination[Person]:
    return await paginator(limit=limit, offset=offset)


sqlalchemy_config = SQLAlchemyConfig(
    connection_string="sqlite+aiosqlite:///test.sqlite", dependency_key="async_session"
)  # Create 'async_session' dependency.
sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)


async def on_startup() -> None:
    """Initializes the database."""
    async with sqlalchemy_config.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app = Starlite(route_handlers=[people_handler], on_startup=[on_startup], plugins=[sqlalchemy_plugin])
