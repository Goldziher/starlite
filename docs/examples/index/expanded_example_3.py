from typing import List

from my_app.models import PartialUserDTO, User
from pydantic import UUID4

from litestar import Controller, delete, get, patch, post, put
from litestar.dto import DTOData


class UserController(Controller):
    path = "/users"

    @post()
    async def create_user(self, data: User) -> User: ...

    @get()
    async def list_users(self) -> List[User]: ...

    @patch(path="/{user_id:uuid}", dto=PartialUserDTO)
    async def partial_update_user(self, user_id: UUID4, data: DTOData[User]) -> User: ...

    @put(path="/{user_id:uuid}")
    async def update_user(self, user_id: UUID4, data: User) -> User: ...

    @get(path="/{user_id:uuid}")
    async def get_user(self, user_id: UUID4) -> User: ...

    @delete(path="/{user_id:uuid}")
    async def delete_user(self, user_id: UUID4) -> None: ...
