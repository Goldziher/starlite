import anyio
from my_app.security.authentication_middleware import JWTAuthenticationMiddleware

from litestar import Litestar, MediaType, Response, get
from litestar.exceptions import NotFoundException
from litestar.middleware.base import DefineMiddleware

# you can optionally exclude certain paths from authentication.
# the following excludes all routes mounted at or under `/schema*`
# additionally,
# you can modify the default exclude key of "exclude_from_auth", by overriding the `exclude_from_auth_key` parameter on the Authentication Middleware
auth_mw = DefineMiddleware(JWTAuthenticationMiddleware, exclude="schema")


@get(path="/", exclude_from_auth=True)
async def site_index() -> Response:
    """Site index"""
    exists = await anyio.Path("index.html").exists()
    if exists:
        async with await anyio.open_file(anyio.Path("index.html")) as file:
            content = await file.read()
            return Response(content=content, status_code=200, media_type=MediaType.HTML)
    raise NotFoundException("Site index was not found")


app = Litestar(route_handlers=[site_index], middleware=[auth_mw])
