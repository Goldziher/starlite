import dataclasses
import secrets
from typing import Any

from litestar import Litestar, Request, get
from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTAuth, Token


@dataclasses.dataclass
class User:
    id: str


async def retrieve_user_handler(token: Token, connection: ASGIConnection) -> User:
    return User(id=token.sub)


jwt_auth = JWTAuth[User](
    token_secret=secrets.token_hex(),
    retrieve_user_handler=retrieve_user_handler,
    accepted_audiences=["https://api.testserver.local"],
    accepted_issuers=["https://auth.testserver.local"],
)


@get("/")
def handler(request: Request[User, Token, Any]) -> dict[str, Any]:
    return {"id": request.user.id}


app = Litestar([handler], middleware=[jwt_auth.middleware])
