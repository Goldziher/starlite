from typing import TYPE_CHECKING, Any

import pytest

from litestar import Litestar, get
from litestar.exceptions import ImproperlyConfiguredException
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import RedocRenderPlugin, SwaggerRenderPlugin
from litestar.openapi.spec import Components, Example, OpenAPIHeader, OpenAPIType, Schema

if TYPE_CHECKING:
    from litestar.handlers.http_handlers import HTTPRouteHandler
    from litestar.openapi.plugins import OpenAPIRenderPlugin


def test_merged_components_correct() -> None:
    components_one = Components(headers={"one": OpenAPIHeader()}, schemas={"test": Schema(type=OpenAPIType.STRING)})
    components_two = Components(headers={"two": OpenAPIHeader()})
    components_three = Components(examples={"example-one": Example(summary="an example")})
    config = OpenAPIConfig(
        title="my title", version="1.0.0", components=[components_one, components_two, components_three]
    )
    openapi = config.to_openapi_schema()
    assert openapi.components
    assert openapi.components.to_schema() == {
        "schemas": {"test": {"type": "string"}},
        "examples": {"example-one": {"summary": "an example"}},
        "headers": {
            "one": {
                "required": False,
                "deprecated": False,
            },
            "two": {
                "required": False,
                "deprecated": False,
            },
        },
    }


def test_allows_customization_of_operation_id_creator() -> None:
    def operation_id_creator(handler: "HTTPRouteHandler", _: Any, __: Any) -> str:
        return f"id_{handler.name}" if handler.name else ""

    @get(path="/1", name="x")
    def handler_1() -> None:
        return

    @get(path="/2", name="y")
    def handler_2() -> None:
        return

    app = Litestar(
        route_handlers=[handler_1, handler_2],
        openapi_config=OpenAPIConfig(title="my title", version="1.0.0", operation_id_creator=operation_id_creator),
    )

    assert app.openapi_schema.to_schema()["paths"] == {
        "/1": {
            "get": {
                "deprecated": False,
                "operationId": "id_x",
                "responses": {"200": {"description": "Request fulfilled, document follows", "headers": {}}},
                "summary": "Handler1",
            }
        },
        "/2": {
            "get": {
                "deprecated": False,
                "operationId": "id_y",
                "responses": {"200": {"description": "Request fulfilled, document follows", "headers": {}}},
                "summary": "Handler2",
            }
        },
    }


def test_raises_exception_when_no_config_in_place() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[], openapi_config=None).update_openapi_schema()


@pytest.mark.parametrize(
    ("plugins", "exp"),
    [
        ((), type(None)),
        ([RedocRenderPlugin()], RedocRenderPlugin),
        ([SwaggerRenderPlugin(), RedocRenderPlugin()], SwaggerRenderPlugin),
        ([RedocRenderPlugin(), SwaggerRenderPlugin(path="/")], SwaggerRenderPlugin),
    ],
)
def test_default_plugin(plugins: "list[OpenAPIRenderPlugin]", exp: "type[OpenAPIRenderPlugin]") -> None:
    config = OpenAPIConfig(title="my title", version="1.0.0", render_plugins=plugins)
    assert isinstance(config.default_plugin, exp)
