from litestar import Request, get


def key_builder(request: Request) -> str:
    return request.url.path + request.headers.get("my-header", "")


@get("/cached-path", cache=True, cache_key_builder=key_builder)
def cached_handler() -> str: ...
