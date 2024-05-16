from litestar import get


@get("/some-path")
async def my_route_handler() -> None: ...
