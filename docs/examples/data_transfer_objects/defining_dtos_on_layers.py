from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from litestar import Controller, delete, get, post, put
from litestar.app import Litestar
from litestar.dto import DataclassDTO
from litestar.dto.config import DTOConfig


@dataclass
class User:
    name: str
    email: str
    age: int
    id: UUID = field(default_factory=uuid4)


class UserWriteDTO(DataclassDTO[User]):
    config = DTOConfig(exclude={"id"})


class UserReadDTO(DataclassDTO[User]): ...


class UserController(Controller):
    dto = UserWriteDTO
    return_dto = UserReadDTO

    @post("/", sync_to_thread=False)
    def create_user(self, data: User) -> User:
        return data

    @get("/", sync_to_thread=False)
    def get_users(self) -> list[User]:
        return [User(name="Mr Sunglass", email="mr.sunglass@example.com", age=30)]

    @get("/{user_id:uuid}", sync_to_thread=False)
    def get_user(self, user_id: UUID) -> User:
        return User(id=user_id, name="Mr Sunglass", email="mr.sunglass@example.com", age=30)

    @put("/{user_id:uuid}", sync_to_thread=False)
    def update_user(self, data: User) -> User:
        return data

    @delete("/{user_id:uuid}", return_dto=None, sync_to_thread=False)
    def delete_user(self, user_id: UUID) -> None:
        return None


app = Litestar([UserController])
