from my_app.security.authentication_middleware import JWTAuthenticationMiddleware

from litestar import Litestar
from litestar.middleware.base import DefineMiddleware

# you can optionally exclude certain paths from authentication.
# the following excludes all routes mounted at or under `/schema*`
auth_mw = DefineMiddleware(JWTAuthenticationMiddleware, exclude="schema")

app = Litestar(route_handlers=[...], middleware=[auth_mw])
