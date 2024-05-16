from litestar import get


@get(path="/some-path")
async def my_route_handler() -> None: ...
