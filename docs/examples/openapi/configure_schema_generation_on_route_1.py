from litestar import get


@get(path="/some-path", include_in_schema=False)
def my_route_handler() -> None: ...
