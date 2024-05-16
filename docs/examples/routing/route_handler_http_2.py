from litestar import HttpMethod
from litestar.handlers.http_handlers import HTTPRouteHandler


@HTTPRouteHandler(path="/some-path", http_method=[HttpMethod.GET, HttpMethod.POST])
async def my_endpoint() -> None: ...
