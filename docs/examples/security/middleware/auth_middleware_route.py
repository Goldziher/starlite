from my_app.db.models import User
from my_app.security.jwt import Token

from litestar import Request, get
from litestar.datastructures import State


@get("/")
def my_route_handler(request: Request[User, Token, State]) -> None:
    user = request.user  # correctly typed as User
    auth = request.auth  # correctly typed as Token
    assert isinstance(user, User)
    assert isinstance(auth, Token)
