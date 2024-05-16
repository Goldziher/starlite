from litestar import Litestar, Request, get
from litestar.plugins.structlog import StructlogPlugin


@get("/")
def my_router_handler(request: Request) -> None:
    request.logger.info("inside a request")
    return None


structlog_plugin = StructlogPlugin()

app = Litestar(route_handlers=[my_router_handler], plugins=[StructlogPlugin()])
