from litestar import get


@get(
    ["/some-path", "/some-path/{some_id:int}"],
)
async def my_route_handler(some_id: int = 1) -> None: ...
