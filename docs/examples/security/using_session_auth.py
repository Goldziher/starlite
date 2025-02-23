from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, SecretStr

from litestar import Litestar, Request, get, post
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.session.server_side import ServerSideSessionBackend, ServerSideSessionConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.security.session_auth import SessionAuth
from litestar.stores.memory import MemoryStore


# Let's assume we have a User model that is a pydantic model.
# This though is not required - we need some sort of user class -
# but it can be any arbitrary value, e.g. an SQLAlchemy model,
# a representation of a MongoDB  etc.
class User(BaseModel):
    id: UUID
    name: str
    email: EmailStr


# we also have pydantic types for two different
# kinds of POST request bodies: one for creating
# a user, e.g. "sign-up", and the other for logging
# an existing user in.
class UserCreatePayload(BaseModel):
    name: str
    email: EmailStr
    password: SecretStr


class UserLoginPayload(BaseModel):
    email: EmailStr
    password: SecretStr


MOCK_DB: dict[str, User] = {}
memory_store = MemoryStore()


# The SessionAuth class requires a handler callable
# that takes the session dictionary, and returns the
# 'User' instance correlating to it.
#
# The session dictionary itself is a value the user decides
# upon. So for example, it might be a simple dictionary
# that holds a user id, for example: { "id": "abcd123" }
#
# Note: The callable can be either sync or async - both will work.
async def retrieve_user_handler(
    session: dict[str, Any], connection: "ASGIConnection[Any, Any, Any, Any]"
) -> Optional[User]:
    return MOCK_DB.get(user_id) if (user_id := session.get("user_id")) else None


@post("/login")
async def login(data: UserLoginPayload, request: "Request[Any, Any, Any]") -> User:
    # we received log-in data via post.
    # our login handler should retrieve from persistence (a db etc.)
    # the user data and verify that the login details
    # are correct. If we are using passwords, we should check that
    # the password hashes match etc. We will simply assume that we
    # have done all of that we now have a user value:
    user_id = await memory_store.get(data.email)

    if not user_id:
        raise NotAuthorizedException
    user_id = user_id.decode("utf-8")

    # once verified we can create a session.
    # to do this we simply need to call the Litestar
    # 'Request.set_session' method, which accepts either dictionaries
    # or pydantic models. In our case, we can simply record a
    # simple dictionary with the user ID value:
    request.set_session({"user_id": user_id})

    # you can do whatever we want here. In this case, we will simply return the user data:
    return MOCK_DB[user_id]


@post("/signup")
async def signup(data: UserCreatePayload, request: Request[Any, Any, Any]) -> User:
    # this is similar to the login handler, except here we should
    # insert into persistence - after doing whatever extra
    # validation we might require. We will assume that this is done,
    # and we now have a user instance with an assigned ID value:
    user = User(name=data.name, email=data.email, id=uuid4())

    await memory_store.set(data.email, str(user.id))
    MOCK_DB[str(user.id)] = user
    # we are creating a session the same as we do in the
    # 'login_handler' above:
    request.set_session({"user_id": str(user.id)})

    # and again, you can add whatever logic is required here, we
    # will simply return the user:
    return user


# the endpoint below requires the user to be already authenticated
# to be able to access it.
@get("/user", sync_to_thread=False)
def get_user(request: Request[User, dict[Literal["user_id"], str], Any]) -> Any:
    # because this route requires authentication, we can access
    # `request.user`, which is the authenticated user returned
    # by the 'retrieve_user_handler' function we passed to SessionAuth.
    return request.user


# We add the session security schema to the OpenAPI config.
openapi_config = OpenAPIConfig(
    title="My API",
    version="1.0.0",
)

session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,
    # we must pass a config for a session backend.
    # all session backends are supported
    session_backend_config=ServerSideSessionConfig(),
    # exclude any URLs that should not have authentication.
    # We exclude the documentation URLs, signup and login.
    exclude=["/login", "/signup", "/schema"],
)


# We initialize the app instance, passing to it the 'session_auth.on_app_init' and the 'openapi_config'.
app = Litestar(
    route_handlers=[login, signup, get_user],
    on_app_init=[session_auth.on_app_init],
    openapi_config=openapi_config,
)
