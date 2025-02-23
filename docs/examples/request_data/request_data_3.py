from dataclasses import dataclass
from typing import Annotated

from litestar import Litestar, post
from litestar.params import Body


@dataclass
class User:
    id: int
    name: str


@post(path="/")
async def create_user(
    data: Annotated[User, Body(title="Create User", description="Create a new user.")],
) -> User:
    return data


app = Litestar(route_handlers=[create_user])
