from typing import Dict

from litestar import Litestar, Request, get
from litestar.logging.config import StructLoggingConfig
from litestar.middleware.logging import LoggingMiddlewareConfig


@get("/")
async def handler(request: Request) -> Dict[str, str]:
    request.logger.info("Logging in the handler")
    return {"hello": "world"}


logging_middleware_config = LoggingMiddlewareConfig()

app = Litestar(
    route_handlers=[handler],
    logging_config=StructLoggingConfig(log_exceptions="always"),
    middleware=[logging_middleware_config.middleware],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
