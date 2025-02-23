from os import environ
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from litestar import Litestar, Request, Response, get, post
from litestar.connection import ASGIConnection
from litestar.openapi.config import OpenAPIConfig
from litestar.security.jwt import JWTAuth, Token


# Let's assume we have a User model that is a pydantic model.
# This though is not required - we need some sort of user class -
# but it can be any arbitrary value, e.g. an SQLAlchemy model, a representation of a MongoDB  etc.
class User(BaseModel):
    id: UUID
    name: str
    email: EmailStr


MOCK_DB: dict[str, User] = {}
BLOCKLIST: dict[str, str] = {}


# JWTAuth requires a retrieve handler callable that receives the JWT token model and the ASGI connection
# and returns the 'User' instance correlating to it.
#
# Notes:
# - 'User' can be any arbitrary value you decide upon.
# - The callable can be either sync or async - both will work.
async def retrieve_user_handler(token: Token, connection: "ASGIConnection[Any, Any, Any, Any]") -> Optional[User]:
    # logic here to retrieve the user instance
    return MOCK_DB.get(token.sub)


# If you want to use JWTAuth with revoking tokens, you have to define a handler of revoked tokens
# with your custom logic.
async def revoked_token_handler(token: Token, connection: "ASGIConnection[Any, Any, Any, Any]") -> bool:
    jti = token.jti  # Unique token identifier (JWT ID)
    if jti:
        # Check if the token is already revoked in the BLOCKLIST
        revoked = BLOCKLIST.get(jti)
        if revoked:
            return True
    return False


jwt_auth = JWTAuth[User](
    retrieve_user_handler=retrieve_user_handler,
    revoked_token_handler=revoked_token_handler,
    token_secret=environ.get("JWT_SECRET", "abcd123"),
    # we are specifying which endpoints should be excluded from authentication. In this case the login endpoint
    # and our openAPI docs.
    exclude=["/login", "/schema"],
)


# Given an instance of 'JWTAuth' we can create a login handler function:
@post("/login")
async def login_handler(data: User) -> Response[User]:
    MOCK_DB[str(data.id)] = data
    # you can do whatever you want to update the response instance here
    # e.g. response.set_cookie(...)
    return jwt_auth.login(identifier=str(data.id), token_extras={"email": data.email}, response_body=data)


# Also we can create a logout
@post("/logout")
async def logout_handler(request: Request["User", Token, Any]) -> dict[str, str]:
    # Your custom logic here
    # For example
    jti = request.auth.jti
    if jti:
        BLOCKLIST[jti] = "revoked"
        return {"message": "Token has been revoked."}
    return {"message": "No valid token found."}


# We also have some other routes, for example:
@get("/some-path", sync_to_thread=False, middleware=[jwt_auth.middleware])
def some_route_handler(request: "Request[User, Token, Any]") -> Any:
    # request.user is set to the instance of user returned by the middleware
    assert isinstance(request.user, User)
    # request.auth is the instance of 'litestar.security.jwt.Token' created from the data encoded in the auth header
    assert isinstance(request.auth, Token)
    # do stuff ...


# We create our OpenAPIConfig as usual - the JWT security scheme will be injected into it.
openapi_config = OpenAPIConfig(
    title="My API",
    version="1.0.0",
)

# We initialize the app instance and pass the jwt_auth 'on_app_init' handler to the constructor.
# The hook handler will inject the JWT middleware and openapi configuration into the app.
app = Litestar(
    route_handlers=[login_handler, logout_handler, some_route_handler],
    on_app_init=[jwt_auth.on_app_init],
    openapi_config=openapi_config,
)
