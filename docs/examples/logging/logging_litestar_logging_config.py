import logging

from litestar import Litestar, Request, get


def get_logger(mod_name: str) -> logging.Logger:
    """Return logger object."""
    format = "%(asctime)s: %(name)s: %(levelname)s: %(message)s"
    logger = logging.getLogger(mod_name)
    # Writes to stdout
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(format))
    logger.addHandler(ch)
    return logger


logger = get_logger(__name__)


@get("/")
def my_router_handler(request: Request) -> None:
    logger.info("logger inside a request")


app = Litestar(
    route_handlers=[my_router_handler],
)
