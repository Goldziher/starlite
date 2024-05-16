from litestar import get


@get("/cached-path", cache=120)  # seconds
def my_cached_handler() -> str: ...
