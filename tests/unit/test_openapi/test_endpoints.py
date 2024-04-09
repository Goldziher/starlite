from typing import List, Optional, Type

import pytest

from litestar import Controller
from litestar.enums import MediaType
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.controller import OpenAPIController
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

root_paths: List[str] = ["", "/part1", "/part1/part2"]


@pytest.fixture()
def config(openapi_controller: Optional[Type[OpenAPIController]]) -> OpenAPIConfig:
    return OpenAPIConfig(title="Litestar API", version="1.0.0", openapi_controller=openapi_controller)


def test_default_redoc_cdn_urls(
    person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    default_redoc_version = "next"
    default_redoc_js_bundle = f"https://cdn.jsdelivr.net/npm/redoc@{default_redoc_version}/bundles/redoc.standalone.js"
    with create_test_client([person_controller, pet_controller], openapi_config=config) as client:
        response = client.get("/schema/redoc")
        assert default_redoc_js_bundle in response.text


def test_default_swagger_ui_cdn_urls(
    person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    default_swagger_ui_version = "5.1.3"
    default_swagger_bundles = [
        f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{default_swagger_ui_version}/swagger-ui.css",
        f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{default_swagger_ui_version}/swagger-ui-bundle.js",
        f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{default_swagger_ui_version}/swagger-ui-standalone-preset.js",
    ]
    with create_test_client([person_controller, pet_controller], openapi_config=config) as client:
        response = client.get("/schema/swagger")
        assert all(cdn_url in response.text for cdn_url in default_swagger_bundles)


def test_default_stoplight_elements_cdn_urls(
    person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    default_stoplight_elements_version = "7.7.18"
    default_stoplight_elements_bundles = [
        f"https://unpkg.com/@stoplight/elements@{default_stoplight_elements_version}/styles.min.css",
        f"https://unpkg.com/@stoplight/elements@{default_stoplight_elements_version}/web-components.min.js",
    ]
    with create_test_client([person_controller, pet_controller], openapi_config=config) as client:
        response = client.get("/schema/elements")
        assert all(cdn_url in response.text for cdn_url in default_stoplight_elements_bundles)


def test_default_rapidoc_elements_cdn_urls(
    person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    default_rapidoc_version = "9.3.4"
    default_rapidoc_bundles = [f"https://unpkg.com/rapidoc@{default_rapidoc_version}/dist/rapidoc-min.js"]
    with create_test_client([person_controller, pet_controller], openapi_config=config) as client:
        response = client.get("/schema/rapidoc")
        assert all(cdn_url in response.text for cdn_url in default_rapidoc_bundles)


def test_redoc_with_google_fonts(
    person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    google_font_cdn = "https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700"
    with create_test_client([person_controller, pet_controller], openapi_config=config) as client:
        response = client.get("/schema/redoc")
        assert google_font_cdn in response.text


@pytest.mark.parametrize(
    ("openapi_controller", "render_plugins"),
    [
        (type("OfflineOpenAPIController", (OpenAPIController,), {"redoc_google_fonts": False}), []),
        (None, [RedocRenderPlugin(google_fonts=False)]),
    ],
)
def test_redoc_without_google_fonts(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
    render_plugins: List[OpenAPIRenderPlugin],
) -> None:
    offline_config = OpenAPIConfig(
        title="Litestar API", version="1.0.0", openapi_controller=openapi_controller, render_plugins=render_plugins
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/redoc")
        assert "fonts.googleapis.com" not in response.text


OFFLINE_LOCATION_JS_URL = "https://offline_location/bundle.js"
OFFLINE_LOCATION_CSS_URL = "https://offline_location/bundle.css"
OFFLINE_LOCATION_OTHER_URL = "https://offline_location/bundle.other"


@pytest.mark.parametrize(
    ("openapi_controller", "render_plugins"),
    [
        (type("OfflineOpenAPIController", (OpenAPIController,), {"redoc_js_url": OFFLINE_LOCATION_JS_URL}), []),
        (None, [RedocRenderPlugin(js_url=OFFLINE_LOCATION_JS_URL)]),
    ],
)
def test_openapi_redoc_offline(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
    render_plugins: List[OpenAPIRenderPlugin],
) -> None:
    offline_config = OpenAPIConfig(
        title="Litestar API", version="1.0.0", openapi_controller=openapi_controller, render_plugins=render_plugins
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/redoc")
        assert OFFLINE_LOCATION_JS_URL in response.text


@pytest.mark.parametrize(
    ("openapi_controller", "render_plugins"),
    [
        (
            type(
                "OfflineOpenAPIController",
                (OpenAPIController,),
                {
                    "swagger_ui_bundle_js_url": OFFLINE_LOCATION_JS_URL,
                    "swagger_css_url": OFFLINE_LOCATION_CSS_URL,
                    "swagger_ui_standalone_preset_js_url": OFFLINE_LOCATION_OTHER_URL,
                },
            ),
            [],
        ),
        (
            None,
            [
                SwaggerRenderPlugin(
                    js_url=OFFLINE_LOCATION_JS_URL,
                    css_url=OFFLINE_LOCATION_CSS_URL,
                    standalone_preset_js_url=OFFLINE_LOCATION_OTHER_URL,
                )
            ],
        ),
    ],
)
def test_openapi_swagger_offline(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
    render_plugins: List[OpenAPIRenderPlugin],
) -> None:
    offline_config = OpenAPIConfig(
        title="Litestar API", version="1.0.0", openapi_controller=openapi_controller, render_plugins=render_plugins
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/swagger")
        assert all(
            offline_url in response.text
            for offline_url in [OFFLINE_LOCATION_JS_URL, OFFLINE_LOCATION_CSS_URL, OFFLINE_LOCATION_OTHER_URL]
        )


@pytest.mark.parametrize(
    ("openapi_controller", "render_plugins"),
    [
        (
            type(
                "OfflineOpenAPIController",
                (OpenAPIController,),
                {
                    "stoplight_elements_css_url": OFFLINE_LOCATION_CSS_URL,
                    "stoplight_elements_js_url": OFFLINE_LOCATION_JS_URL,
                },
            ),
            [],
        ),
        (
            None,
            [
                StoplightRenderPlugin(
                    js_url=OFFLINE_LOCATION_JS_URL,
                    css_url=OFFLINE_LOCATION_CSS_URL,
                )
            ],
        ),
    ],
)
def test_openapi_stoplight_elements_offline(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
    render_plugins: List[OpenAPIRenderPlugin],
) -> None:
    offline_config = OpenAPIConfig(
        title="Litestar API", version="1.0.0", openapi_controller=openapi_controller, render_plugins=render_plugins
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/elements")
        assert all(offline_url in response.text for offline_url in [OFFLINE_LOCATION_JS_URL, OFFLINE_LOCATION_CSS_URL])


@pytest.mark.parametrize(
    ("openapi_controller", "render_plugins"),
    [
        (
            None,
            [
                ScalarRenderPlugin(
                    js_url=OFFLINE_LOCATION_JS_URL,
                    css_url=OFFLINE_LOCATION_CSS_URL,
                )
            ],
        ),
    ],
)
def test_openapi_scalar_offline(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
    render_plugins: List[OpenAPIRenderPlugin],
) -> None:
    offline_config = OpenAPIConfig(
        title="Litestar API", version="1.0.0", openapi_controller=openapi_controller, render_plugins=render_plugins
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/scalar")
        assert all(offline_url in response.text for offline_url in [OFFLINE_LOCATION_JS_URL, OFFLINE_LOCATION_CSS_URL])


@pytest.mark.parametrize(
    ("openapi_controller", "render_plugins"),
    [
        (type("OfflineOpenAPIController", (OpenAPIController,), {"rapidoc_js_url": OFFLINE_LOCATION_JS_URL}), []),
        (None, [RapidocRenderPlugin(js_url=OFFLINE_LOCATION_JS_URL)]),
    ],
)
def test_openapi_rapidoc_offline(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
    render_plugins: List[OpenAPIRenderPlugin],
) -> None:
    offline_config = OpenAPIConfig(
        title="Litestar API", version="1.0.0", openapi_controller=openapi_controller, render_plugins=render_plugins
    )
    with create_test_client([person_controller, pet_controller], openapi_config=offline_config) as client:
        response = client.get("/schema/rapidoc")
        assert OFFLINE_LOCATION_JS_URL in response.text


@pytest.mark.parametrize("root_path", root_paths)
def test_openapi_root(
    root_path: str, person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    with create_test_client([person_controller, pet_controller], root_path=root_path, openapi_config=config) as client:
        response = client.get("/schema")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


@pytest.mark.parametrize("root_path", root_paths)
def test_openapi_redoc(
    root_path: str, person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    with create_test_client([person_controller, pet_controller], root_path=root_path, openapi_config=config) as client:
        response = client.get("/schema/redoc")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


@pytest.mark.parametrize("root_path", root_paths)
def test_openapi_swagger(
    root_path: str, person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    with create_test_client([person_controller, pet_controller], root_path=root_path, openapi_config=config) as client:
        response = client.get("/schema/swagger")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


@pytest.mark.parametrize("root_path", root_paths)
def test_openapi_swagger_caching_schema(
    root_path: str, person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    with create_test_client([person_controller, pet_controller], root_path=root_path, openapi_config=config) as client:
        # Make sure that the schema is tweaked for swagger as the openapi version is changed.
        # Because schema can get cached, make sure that getting a different schema type before works.
        client.get("/schema/redoc")  # Cache the schema
        response = client.get("/schema/swagger")  # Request swagger, should use a different cache

        assert "3.1.0" in response.text  # Make sure the injected version is still there
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


@pytest.mark.parametrize("root_path", root_paths)
def test_openapi_stoplight_elements(
    root_path: str, person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    with create_test_client([person_controller, pet_controller], root_path=root_path, openapi_config=config) as client:
        response = client.get("/schema/elements/")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


@pytest.mark.parametrize("root_path", root_paths)
def test_openapi_rapidoc(
    root_path: str, person_controller: Type[Controller], pet_controller: Type[Controller], config: OpenAPIConfig
) -> None:
    with create_test_client([person_controller, pet_controller], root_path=root_path, openapi_config=config) as client:
        response = client.get("/schema/rapidoc")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


def test_openapi_root_not_allowed(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
) -> None:
    with create_test_client(
        [person_controller, pet_controller],
        openapi_config=OpenAPIConfig(
            title="Litestar API",
            version="1.0.0",
            enabled_endpoints={"swagger", "elements", "openapi.json", "openapi.yaml", "openapi.yml"},
            openapi_controller=openapi_controller,
        ),
    ) as client:
        response = client.get("/schema")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


def test_openapi_redoc_not_allowed(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
) -> None:
    with create_test_client(
        [person_controller, pet_controller],
        openapi_config=OpenAPIConfig(
            title="Litestar API",
            version="1.0.0",
            enabled_endpoints={"swagger", "elements", "openapi.json", "openapi.yaml", "openapi.yml"},
            openapi_controller=openapi_controller,
        ),
    ) as client:
        response = client.get("/schema/redoc")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


def test_openapi_swagger_not_allowed(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
) -> None:
    with create_test_client(
        [person_controller, pet_controller],
        openapi_config=OpenAPIConfig(
            title="Litestar API",
            version="1.0.0",
            enabled_endpoints={"redoc", "elements", "openapi.json", "openapi.yaml", "openapi.yml"},
            openapi_controller=openapi_controller,
        ),
    ) as client:
        response = client.get("/schema/swagger")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


def test_openapi_stoplight_elements_not_allowed(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
) -> None:
    with create_test_client(
        [person_controller, pet_controller],
        openapi_config=OpenAPIConfig(
            title="Litestar API",
            version="1.0.0",
            enabled_endpoints={"redoc", "swagger", "openapi.json", "openapi.yaml", "openapi.yml"},
            openapi_controller=openapi_controller,
        ),
    ) as client:
        response = client.get("/schema/elements/")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


def test_openapi_rapidoc_not_allowed(
    person_controller: Type[Controller],
    pet_controller: Type[Controller],
    openapi_controller: Optional[Type[OpenAPIController]],
) -> None:
    with create_test_client(
        [person_controller, pet_controller],
        openapi_config=OpenAPIConfig(
            title="Litestar API",
            version="1.0.0",
            enabled_endpoints={"swagger", "elements", "openapi.json", "openapi.yaml", "openapi.yml"},
            openapi_controller=openapi_controller,
        ),
    ) as client:
        response = client.get("/schema/rapidoc")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.headers["content-type"].startswith(MediaType.HTML.value)


@pytest.mark.parametrize(
    ("render_plugins",),
    [
        ([],),
        ([RedocRenderPlugin()],),
        ([RedocRenderPlugin(), JsonRenderPlugin()],),
        ([JsonRenderPlugin(path="/custom_path")],),
        ([JsonRenderPlugin(path=["/openapi.json", "/custom_path"])],),
    ],
)
def test_json_plugin_always_enabled(render_plugins: List["OpenAPIRenderPlugin"]) -> None:
    """We assume that an '/openapi.json' path is available in many of the openapi render plugins.

    This test ensures that the json plugin is always enabled, even if the user has not explicitly
    included it in the render_plugins list.
    """

    openapi_config = OpenAPIConfig(title="my title", version="1.0.0", render_plugins=render_plugins)
    with create_test_client([], openapi_config=openapi_config) as client:
        response = client.get("/schema/openapi.json")
        assert response.status_code == HTTP_200_OK


def test_default_plugin_explicit_path() -> None:
    config = OpenAPIConfig(title="my title", version="1.0.0", render_plugins=[SwaggerRenderPlugin(path="/")])
    with create_test_client([], openapi_config=config) as client:
        response = client.get("/schema/")
        assert response.status_code == HTTP_200_OK

        response = client.get("/schema/swagger")
        assert response.status_code == HTTP_404_NOT_FOUND


def test_default_plugin_backward_compatibility() -> None:
    config = OpenAPIConfig(title="my title", version="1.0.0")
    with create_test_client([], openapi_config=config) as client:
        response = client.get("/schema/")
        assert response.status_code == HTTP_200_OK

        response = client.get("/schema/redoc")
        assert response.status_code == HTTP_200_OK


def test_default_plugin_backward_compatibility_not_found() -> None:
    config = OpenAPIConfig(title="my title", version="1.0.0", enabled_endpoints={"redoc"}, root_schema_site="swagger")
    with create_test_client([], openapi_config=config) as client:
        response = client.get("/schema/")
        assert response.status_code == HTTP_404_NOT_FOUND

        response = client.get("/schema/swagger")
        assert response.status_code == HTTP_404_NOT_FOUND

        response = client.get("/schema/redoc")
        assert response.status_code == HTTP_200_OK


def test_default_plugin_future_compatibility() -> None:
    config = OpenAPIConfig(title="my title", version="1.0.0", render_plugins=[SwaggerRenderPlugin()])
    with create_test_client([], openapi_config=config) as client:
        response = client.get("/schema/")
        assert response.status_code == HTTP_200_OK

        response = client.get("/schema/swagger")
        assert response.status_code == HTTP_200_OK
