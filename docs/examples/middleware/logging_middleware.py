from typing import Dict

from starlite import Starlite, get
from starlite.config.logging import LoggingConfig
from starlite.middleware import LoggingMiddlewareConfig

logging_middleware_config = LoggingMiddlewareConfig()


@get("/")
def my_handler() -> Dict[str, str]:
    return {"hello": "world"}


app = Starlite(
    route_handlers=[my_handler],
    logging_config=LoggingConfig(),
    middleware=[logging_middleware_config.middleware],
)
