from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from litestar import Litestar, post
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyInitPlugin, SQLAlchemySyncConfig

if TYPE_CHECKING:
    from typing import Any, Dict, List

    from sqlalchemy.orm import Session


class Base(DeclarativeBase): ...


class TodoItem(Base):
    __tablename__ = "todo_item"
    title: Mapped[str] = mapped_column(primary_key=True)
    done: Mapped[bool]


@post("/", sync_to_thread=True)
def add_item(data: Dict[str, Any], db_session: Session) -> List[Dict[str, Any]]:
    todo_item = TodoItem(**data)
    with db_session.begin():
        db_session.add(todo_item)
    return [
        {
            "title": item.title,
            "done": item.done,
        }
        for item in db_session.execute(select(TodoItem)).scalars()
    ]


def init_db(app: Litestar) -> None:
    Base.metadata.drop_all(app.state.db_engine)
    Base.metadata.create_all(app.state.db_engine)


config = SQLAlchemySyncConfig(connection_string="sqlite:///todo_sync.sqlite")
plugin = SQLAlchemyInitPlugin(config=config)
app = Litestar(route_handlers=[add_item], plugins=[plugin], on_startup=[init_db])
