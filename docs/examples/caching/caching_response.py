from litestar import get


@get("/cached-path", cache=True)
def my_cached_handler() -> str: ...
