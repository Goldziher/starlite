from pydantic import UUID4, BaseModel

from litestar import Controller, patch
from litestar.di import Provide


class User(BaseModel):
    id: UUID4
    name: str


async def retrieve_db_user(user_id: UUID4) -> User: ...


class UserController(Controller):
    path = "/user"
    dependencies = {"user": Provide(retrieve_db_user)}

    @patch(path="/{user_id:uuid}")
    async def get_user(self, user: User) -> User: ...
