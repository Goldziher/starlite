from typing import TYPE_CHECKING, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Mapped

from litestar import Litestar, get
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin
from litestar.di import Provide
from litestar.pagination import AbstractAsyncOffsetPaginator, OffsetPagination

if TYPE_CHECKING:
    from sqlalchemy.engine.result import ScalarResult
    from sqlalchemy.ext.asyncio import AsyncSession


class Person(UUIDBase):
    name: Mapped[str]


class PersonOffsetPaginator(AbstractAsyncOffsetPaginator[Person]):
    def __init__(self, async_session: AsyncSession) -> None:  # 'async_session' dependency will be injected here.
        self.async_session = async_session

    async def get_total(self) -> int:
        return cast("int", await self.async_session.scalar(select(func.count(Person.id))))

    async def get_items(self, limit: int, offset: int) -> list[Person]:
        people: ScalarResult = await self.async_session.scalars(select(Person).slice(offset, limit))
        return list(people.all())


# Create a route handler. The handler will receive two query parameters - 'limit' and 'offset', which is passed
# to the paginator instance. Also create a dependency 'paginator' which will be injected into the handler.
@get("/people", dependencies={"paginator": Provide(PersonOffsetPaginator)})
async def people_handler(paginator: PersonOffsetPaginator, limit: int, offset: int) -> OffsetPagination[Person]:
    return await paginator(limit=limit, offset=offset)


sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///test.sqlite", session_dependency_key="async_session"
)  # Create 'async_session' dependency.
sqlalchemy_plugin = SQLAlchemyInitPlugin(config=sqlalchemy_config)


async def on_startup() -> None:
    """Initializes the database."""
    async with sqlalchemy_config.get_engine().begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)


app = Litestar(route_handlers=[people_handler], on_startup=[on_startup], plugins=[sqlalchemy_plugin])
