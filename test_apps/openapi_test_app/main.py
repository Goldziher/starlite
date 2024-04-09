from __future__ import annotations

import msgspec

from litestar import Litestar, get
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from tests.unit.test_openapi.conftest import create_person_controller, create_pet_controller


class Model(msgspec.Struct):
    hello: str = "world"


@get("/", sync_to_thread=False)
def greet() -> Model:
    return Model(hello="world")


app = Litestar(
    route_handlers=[greet, create_person_controller(), create_pet_controller()],
    openapi_config=OpenAPIConfig(
        title="whatever",
        version="0.0.1",
        render_plugins=[ScalarRenderPlugin()],
    ),
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
