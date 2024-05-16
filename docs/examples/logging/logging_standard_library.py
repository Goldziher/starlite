import logging

from litestar import Litestar, Request, get
from litestar.logging import LoggingConfig

logging_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.INFO), "handlers": ["console"]},
    formatters={"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
)

logger = logging_config.configure()()


@get("/")
def my_router_handler(request: Request) -> None:
    request.logger.info("inside a request")
    logger.info("here too")


app = Litestar(
    route_handlers=[my_router_handler],
    logging_config=logging_config,
)
