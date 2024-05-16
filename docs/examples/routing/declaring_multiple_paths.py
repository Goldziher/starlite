from litestar import get


@get(["/some-path", "/some-other-path"])
async def my_route_handler() -> None: ...
