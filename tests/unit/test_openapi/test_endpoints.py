from collections.abc import Callable, Sequence

import pytest
from typing_extensions import ParamSpec, TypeAlias

from litestar import Controller
from litestar.enums import MediaType
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import (
    JsonRenderPlugin,
    OpenAPIRenderPlugin,
    RapidocRenderPlugin,
    RedocRenderPlugin,
    ScalarRenderPlugin,
    StoplightRenderPlugin,
    SwaggerRenderPlugin,
)
from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from litestar.testing import create_test_client

root_paths: list[str] = ["", "/part1", "/part1/part2"]

P = ParamSpec("P")
ConfigFactoryType: TypeAlias = "Callable[[Sequence[OpenAPIRenderPlugin]], OpenAPIConfig]"


@pytest.fixture()
def config_factory() -> ConfigFactoryType:
    def factory(render_plugins: Sequence[OpenAPIRenderPlugin]) -> OpenAPIConfig:
        return OpenAPIConfig(title="Litestar API", version="1.0.0", render_plugins=list(render_plugins))

    return factory


def test_default_redoc_cdn_urls(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    default_redoc_version = "next"
    default_redoc_js_bundle = f"https://cdn.jsdelivr.net/npm/redoc@{default_redoc_version}/bundles/redoc.standalone.js"
    with create_test_client(
        [person_controller, pet_controller], openapi_config=config_factory((RedocRenderPlugin(),))
    ) as client:
        response = client.get("/schema/redoc")
        assert default_redoc_js_bundle in response.text


def test_default_swagger_ui_cdn_urls(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    default_swagger_ui_version = "5.18.2"
    default_swagger_bundles = [
        f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{default_swagger_ui_version}/swagger-ui.css",
        f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{default_swagger_ui_version}/swagger-ui-bundle.js",
        f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{default_swagger_ui_version}/swagger-ui-standalone-preset.js",
    ]
    with create_test_client(
        [person_controller, pet_controller], openapi_config=config_factory((SwaggerRenderPlugin(),))
    ) as client:
        response = client.get("/schema/swagger")
        assert all(cdn_url in response.text for cdn_url in default_swagger_bundles)


def test_default_stoplight_elements_cdn_urls(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    default_stoplight_elements_version = "7.7.18"
    default_stoplight_elements_bundles = [
        f"https://unpkg.com/@stoplight/elements@{default_stoplight_elements_version}/styles.min.css",
        f"https://unpkg.com/@stoplight/elements@{default_stoplight_elements_version}/web-components.min.js",
    ]
    with create_test_client(
        [person_controller, pet_controller], openapi_config=config_factory((StoplightRenderPlugin(),))
    ) as client:
        response = client.get("/schema/elements")
        assert all(cdn_url in response.text for cdn_url in default_stoplight_elements_bundles)


def test_default_rapidoc_elements_cdn_urls(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    default_rapidoc_version = "9.3.4"
    default_rapidoc_bundles = [f"https://unpkg.com/rapidoc@{default_rapidoc_version}/dist/rapidoc-min.js"]
    with create_test_client(
        [person_controller, pet_controller], openapi_config=config_factory((RapidocRenderPlugin(),))
    ) as client:
        response = client.get("/schema/rapidoc")
        assert all(cdn_url in response.text for cdn_url in default_rapidoc_bundles)


def test_redoc_with_google_fonts(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    google_font_cdn = "https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700"
    with create_test_client(
        [person_controller, pet_controller], openapi_config=config_factory((RedocRenderPlugin(),))
    ) as client:
        response = client.get("/schema/redoc")
        assert google_font_cdn in response.text


def test_redoc_without_google_fonts(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    offline_config = config_factory((RedocRenderPlugin(google_fonts=False),))
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/redoc")
        assert "fonts.googleapis.com" not in response.text


OFFLINE_LOCATION_JS_URL = "https://offline_location/bundle.js"
OFFLINE_LOCATION_CSS_URL = "https://offline_location/bundle.css"
OFFLINE_LOCATION_OTHER_URL = "https://offline_location/bundle.other"


def test_openapi_redoc_offline(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    offline_config = config_factory((RedocRenderPlugin(js_url=OFFLINE_LOCATION_JS_URL),))
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/redoc")
        assert OFFLINE_LOCATION_JS_URL in response.text


def test_openapi_swagger_offline(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    offline_config = config_factory(
        (
            SwaggerRenderPlugin(
                js_url=OFFLINE_LOCATION_JS_URL,
                css_url=OFFLINE_LOCATION_CSS_URL,
                standalone_preset_js_url=OFFLINE_LOCATION_OTHER_URL,
            ),
        )
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/swagger")
        assert all(
            offline_url in response.text
            for offline_url in [OFFLINE_LOCATION_JS_URL, OFFLINE_LOCATION_CSS_URL, OFFLINE_LOCATION_OTHER_URL]
        )


def test_openapi_stoplight_elements_offline(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    offline_config = config_factory(
        (StoplightRenderPlugin(js_url=OFFLINE_LOCATION_JS_URL, css_url=OFFLINE_LOCATION_CSS_URL),)
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/elements")
        assert all(offline_url in response.text for offline_url in [OFFLINE_LOCATION_JS_URL, OFFLINE_LOCATION_CSS_URL])


def test_openapi_scalar_offline(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    offline_config = config_factory(
        (ScalarRenderPlugin(js_url=OFFLINE_LOCATION_JS_URL, css_url=OFFLINE_LOCATION_CSS_URL),)
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/scalar")
        assert all(offline_url in response.text for offline_url in [OFFLINE_LOCATION_JS_URL, OFFLINE_LOCATION_CSS_URL])


def test_openapi_rapidoc_offline(
    person_controller: type[Controller], pet_controller: type[Controller], config_factory: ConfigFactoryType
) -> None:
    offline_config = config_factory((RapidocRenderPlugin(js_url=OFFLINE_LOCATION_JS_URL),))
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/rapidoc")
        assert OFFLINE_LOCATION_JS_URL in response.text


@pytest.mark.parametrize("root_path", root_paths)
@pytest.mark.parametrize(
    ("plugin", "path"),
    [
        (RedocRenderPlugin(), "/schema/redoc"),
        (SwaggerRenderPlugin(), "/schema/swagger"),
        (StoplightRenderPlugin(), "/schema/elements"),
        (ScalarRenderPlugin(), "/schema/scalar"),
        (RapidocRenderPlugin(), "/schema/rapidoc"),
    ],
)
def test_openapi_plugins(
    root_path: str,
    plugin: OpenAPIRenderPlugin,
    path: str,
    person_controller: type[Controller],
    pet_controller: type[Controller],
    config_factory: ConfigFactoryType,
) -> None:
    with create_test_client(
        [person_controller, pet_controller], root_path=root_path, openapi_config=config_factory((plugin,))
    ) as client:
        response = client.get("/schema")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)
        response = client.get(path)
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


@pytest.mark.parametrize("root_path", root_paths)
def test_openapi_swagger_caching_schema(
    root_path: str,
    person_controller: type[Controller],
    pet_controller: type[Controller],
    config_factory: ConfigFactoryType,
) -> None:
    with create_test_client(
        [person_controller, pet_controller],
        root_path=root_path,
        openapi_config=config_factory((SwaggerRenderPlugin(),)),
    ) as client:
        # Make sure that the schema is tweaked for swagger as the openapi version is changed.
        # Because schema can get cached, make sure that getting a different schema type before works.
        client.get("/schema/redoc")  # Cache the schema
        response = client.get("/schema/swagger")  # Request swagger, should use a different cache

        assert "3.1.0" in response.text  # Make sure the injected version is still there
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


def test_openapi_plugin_not_found(person_controller: type[Controller], pet_controller: type[Controller]) -> None:
    with create_test_client(
        [person_controller, pet_controller],
        openapi_config=OpenAPIConfig(
            title="Litestar API",
            version="1.0.0",
        ),
    ) as client:
        response = client.get("/schema/rapidoc")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


@pytest.mark.parametrize(
    ("render_plugins",),
    [
        ([],),
        ([ScalarRenderPlugin()],),
        ([ScalarRenderPlugin(), JsonRenderPlugin()],),
        ([JsonRenderPlugin(path="/custom_path")],),
        ([JsonRenderPlugin(path=["/openapi.json", "/custom_path"])],),
    ],
)
def test_json_plugin_always_enabled(render_plugins: list["OpenAPIRenderPlugin"]) -> None:
    """We assume that an '/openapi.json' path is available in many of the openapi render plugins.

    This test ensures that the json plugin is always enabled, even if the user has not explicitly
    included it in the render_plugins list.
    """

    openapi_config = OpenAPIConfig(title="my title", version="1.0.0", render_plugins=render_plugins)
    with create_test_client([], openapi_config=openapi_config) as client:
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_200_OK


def test_plugin_explicit_root_path() -> None:
    config = OpenAPIConfig(title="my title", version="1.0.0", render_plugins=[SwaggerRenderPlugin(path="/")])
    with create_test_client([], openapi_config=config) as client:
        response = client.get("/schema/")
        assert response.status_code == HTTP_200_OK

        response = client.get("/schema/swagger")
        assert response.status_code == HTTP_404_NOT_FOUND


def test_default_plugin() -> None:
    config = OpenAPIConfig(title="my title", version="1.0.0")
    with create_test_client([], openapi_config=config) as client:
        response = client.get("/schema/")
        assert response.status_code == HTTP_200_OK

        response = client.get("/schema/scalar")
        assert response.status_code == HTTP_200_OK


def test_explicit_plugin() -> None:
    config = OpenAPIConfig(title="my title", version="1.0.0", render_plugins=[SwaggerRenderPlugin()])
    with create_test_client([], openapi_config=config) as client:
        response = client.get("/schema/")
        assert response.status_code == HTTP_200_OK

        response = client.get("/schema/swagger")
        assert response.status_code == HTTP_200_OK
