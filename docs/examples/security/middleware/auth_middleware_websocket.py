from my_app.db.models import User
from my_app.security.jwt import Token

from litestar import WebSocket, websocket
from litestar.datastructures import State


@websocket("/")
async def my_route_handler(socket: WebSocket[User, Token, State]) -> None:
    user = socket.user  # correctly typed as User
    auth = socket.auth  # correctly typed as Token
    assert isinstance(user, User)
    assert isinstance(auth, Token)
