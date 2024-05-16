from litestar import Litestar
from litestar.openapi import OpenAPIConfig

app = Litestar(route_handlers=[...], openapi_config=OpenAPIConfig(title="My API", version="1.0.0"))
