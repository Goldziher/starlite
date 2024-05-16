import logging

from litestar import Litestar, Request, get
from litestar.logging import LoggingConfig


@get("/")
def my_router_handler(request: Request) -> None:
    request.logger.info("inside a request")
    return None


logging_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.INFO), "handlers": ["console"]},
    formatters={"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
)

app = Litestar(route_handlers=[my_router_handler], logging_config=logging_config)
