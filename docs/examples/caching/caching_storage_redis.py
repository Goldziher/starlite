from litestar.config.cache import ResponseCacheConfig
from litestar.stores.redis import RedisStore

redis_store = RedisStore(url="redis://localhost/", port=6379, db=0)

cache_config = ResponseCacheConfig(store=redis_store)
