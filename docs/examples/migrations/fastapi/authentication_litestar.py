from litestar import ASGIConnection, BaseRouteHandler, get


async def authenticate(connection: ASGIConnection, route_handler: BaseRouteHandler) -> None: ...


@get("/", guards=[authenticate])
async def index() -> dict[str, str]: ...
