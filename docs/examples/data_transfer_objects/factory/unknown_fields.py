from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from litestar import Litestar, post
from litestar.dto import DataclassDTO, DTOConfig


@dataclass
class User:
    id: str


UserDTO = DataclassDTO[Annotated[User, DTOConfig(forbid_unknown_fields=True)]]


@post("/users", dto=UserDTO)
async def create_user(data: User) -> User:
    return data


app = Litestar([create_user])


# run: /users -H "Content-Type: application/json" -d '{"id": "1", "name": "Peter"}'
