from datetime import datetime

from sqlalchemy.orm import Mapped

from litestar import Litestar, get
from litestar.dto import DTOConfig
from litestar.pagination import ClassicPagination
from litestar.plugins.sqlalchemy import SQLAlchemyDTO, base


class User(base.UUIDBase):
    name: Mapped[str]
    password: Mapped[str]
    created_at: Mapped[datetime]


class UserDTO(SQLAlchemyDTO[User]):
    config = DTOConfig(exclude={"password", "created_at"})


@get("/users", dto=UserDTO, sync_to_thread=False)
def get_users() -> ClassicPagination[User]:
    return ClassicPagination(
        page_size=10,
        total_pages=1,
        current_page=1,
        items=[
            User(
                id=1,
                name="Litestar User",
                password="xyz",
                created_at=datetime.now(),
            ),
        ],
    )


app = Litestar(route_handlers=[get_users])

# run: /users
