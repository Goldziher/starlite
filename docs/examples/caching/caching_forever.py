from litestar import get
from litestar.config.response_cache import CACHE_FOREVER


@get("/cached-path", cache=CACHE_FOREVER)  # seconds
def my_cached_handler() -> str: ...
