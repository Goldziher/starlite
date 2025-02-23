from litestar import Litestar, get
from litestar.logging.config import LoggingConfig
from litestar.middleware.logging import LoggingMiddlewareConfig

logging_middleware_config = LoggingMiddlewareConfig()


@get("/", sync_to_thread=False)
def my_handler() -> dict[str, str]:
    return {"hello": "world"}


app = Litestar(
    route_handlers=[my_handler],
    logging_config=LoggingConfig(),
    middleware=[logging_middleware_config.middleware],
)
