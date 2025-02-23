from dataclasses import dataclass
from typing import Annotated

from litestar import Litestar, post
from litestar.enums import RequestEncodingType
from litestar.params import Body


@dataclass
class User:
    id: int
    name: str


@post(path="/")
async def create_user(
    data: Annotated[User, Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> User:
    return data


app = Litestar(route_handlers=[create_user])
