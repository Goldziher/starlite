from litestar import HttpMethod, route


@route(path="/some-path", http_method=[HttpMethod.GET, HttpMethod.POST])
async def my_endpoint() -> None: ...
