import dataclasses
import secrets
from typing import Any

from litestar import Litestar, Request, get
from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTAuth, Token


@dataclasses.dataclass
class CustomToken(Token):
    token_flag: bool = False


@dataclasses.dataclass
class User:
    id: str


async def retrieve_user_handler(token: CustomToken, connection: ASGIConnection) -> User:
    return User(id=token.sub)


TOKEN_SECRET = secrets.token_hex()

jwt_auth = JWTAuth[User](
    token_secret=TOKEN_SECRET,
    retrieve_user_handler=retrieve_user_handler,
    token_cls=CustomToken,
)


@get("/")
def handler(request: Request[User, CustomToken, Any]) -> dict[str, Any]:
    return {"id": request.user.id, "token_flag": request.auth.token_flag}


app = Litestar(middleware=[jwt_auth.middleware])
