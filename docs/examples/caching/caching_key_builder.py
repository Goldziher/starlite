from litestar import Litestar, Request
from litestar.config.cache import ResponseCacheConfig


def key_builder(request: Request) -> str:
    return request.url.path + request.headers.get("my-header", "")


app = Litestar([], cache_config=ResponseCacheConfig(key_builder=key_builder))
