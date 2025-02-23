from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from litestar import Litestar, post
from litestar.plugins.sqlalchemy import SQLAlchemyInitPlugin, SQLAlchemySyncConfig

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlalchemy.orm import Session


@post("/", sync_to_thread=True)
def handler(db_session: Session, db_engine: Engine) -> tuple[int, int]:
    one = db_session.execute(select(1)).scalar()

    with db_engine.begin() as conn:
        two = conn.execute(select(2)).scalar()

    return one, two


config = SQLAlchemySyncConfig(connection_string="sqlite:///sync.sqlite")
plugin = SQLAlchemyInitPlugin(config=config)
app = Litestar(route_handlers=[handler], plugins=[plugin])
