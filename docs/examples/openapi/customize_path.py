from typing import Dict

from litestar import Litestar, get
from litestar.openapi.config import OpenAPIConfig


@get("/")
def hello_world() -> Dict[str, str]:
    return {"message": "Hello World"}


app = Litestar(
    route_handlers=[hello_world],
    openapi_config=OpenAPIConfig(
        title="My API",
        description="This is the description of my API",
        version="0.1.0",
        path="/docs",
    ),
)
