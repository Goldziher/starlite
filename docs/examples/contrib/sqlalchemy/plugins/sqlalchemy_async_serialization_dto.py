from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from litestar import Litestar, post
from litestar.plugins.sqlalchemy import SQLAlchemyDTO



class Base(DeclarativeBase): ...


class TodoItem(Base):
    __tablename__ = "todo_item"
    title: Mapped[str] = mapped_column(primary_key=True)
    done: Mapped[bool]


@post("/", dto=SQLAlchemyDTO[TodoItem])
async def add_item(data: TodoItem) -> list[TodoItem]:
    return [data]


app = Litestar(route_handlers=[add_item])
