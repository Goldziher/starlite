import html
from os import urandom
from pathlib import Path
from typing import Any, Optional

import pytest
from bs4 import BeautifulSoup

from litestar import MediaType, WebSocket, delete, get, patch, post, put, websocket
from litestar.config.csrf import CSRFConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.contrib.mako import MakoTemplateEngine
from litestar.enums import RequestEncodingType
from litestar.handlers import HTTPRouteHandler
from litestar.params import Body
from litestar.response.template import Template
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from litestar.template.config import TemplateConfig
from litestar.testing import create_test_client


def handler_fn() -> None:
    pass


@pytest.fixture
def get_handler() -> HTTPRouteHandler:
    return get()(handler_fn)


@pytest.fixture
def post_handler() -> HTTPRouteHandler:
    return post()(handler_fn)


@pytest.fixture
def put_handler() -> HTTPRouteHandler:
    return put()(handler_fn)


@pytest.fixture
def delete_handler() -> HTTPRouteHandler:
    return delete()(handler_fn)


@pytest.fixture
def patch_handler() -> HTTPRouteHandler:
    return patch()(handler_fn)


def test_csrf_successful_flow(get_handler: HTTPRouteHandler, post_handler: HTTPRouteHandler) -> None:
    with create_test_client(
        route_handlers=[get_handler, post_handler], csrf_config=CSRFConfig(secret="secret")
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

        csrf_token: Optional[str] = response.cookies.get("csrftoken")
        assert csrf_token is not None

        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header is not None
        assert set_cookie_header.split("; ") == [
            f"csrftoken={csrf_token}",
            "Path=/",
            "SameSite=lax",
        ]

        response = client.post("/", headers={"x-csrftoken": csrf_token})
        assert response.status_code == HTTP_201_CREATED


@pytest.mark.parametrize(
    "method",
    ["POST", "PUT", "DELETE", "PATCH"],
)
def test_unsafe_method_fails_without_csrf_header(
    method: str,
    get_handler: HTTPRouteHandler,
    post_handler: HTTPRouteHandler,
    put_handler: HTTPRouteHandler,
    delete_handler: HTTPRouteHandler,
    patch_handler: HTTPRouteHandler,
) -> None:
    with create_test_client(
        route_handlers=[get_handler, post_handler, put_handler, delete_handler, patch_handler],
        csrf_config=CSRFConfig(secret="secret"),
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

        csrf_token: Optional[str] = response.cookies.get("csrftoken")
        assert csrf_token is not None

        response = client.request(method, "/")
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "CSRF token verification failed", "status_code": 403}


def test_invalid_csrf_token(get_handler: HTTPRouteHandler, post_handler: HTTPRouteHandler) -> None:
    with create_test_client(
        route_handlers=[get_handler, post_handler], csrf_config=CSRFConfig(secret="secret")
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

        csrf_token: Optional[str] = response.cookies.get("csrftoken")
        assert csrf_token is not None

        response = client.post("/", headers={"x-csrftoken": f"{csrf_token}invalid"})
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "CSRF token verification failed", "status_code": 403}


def test_csrf_token_too_short(get_handler: HTTPRouteHandler, post_handler: HTTPRouteHandler) -> None:
    with create_test_client(
        route_handlers=[get_handler, post_handler], csrf_config=CSRFConfig(secret="secret")
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

        assert "csrftoken" in response.cookies

        response = client.post("/", headers={"x-csrftoken": "too-short"})
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "CSRF token verification failed", "status_code": 403}


def test_websocket_ignored() -> None:
    @websocket(path="/")
    async def websocket_handler(socket: WebSocket) -> None:
        await socket.accept()
        await socket.send_json({"data": "123"})
        await socket.close()

    with (
        create_test_client(route_handlers=[websocket_handler], csrf_config=CSRFConfig(secret="secret")) as client,
        client.websocket_connect("/") as ws,
    ):
        response = ws.receive_json()
        assert response is not None


def test_custom_csrf_config(get_handler: HTTPRouteHandler, post_handler: HTTPRouteHandler) -> None:
    with create_test_client(
        base_url="http://test.com",
        route_handlers=[get_handler, post_handler],
        csrf_config=CSRFConfig(
            secret="secret",
            cookie_name="custom-csrftoken",
            header_name="x-custom-csrftoken",
        ),
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

        csrf_token: Optional[str] = response.cookies.get("custom-csrftoken")
        assert csrf_token is not None

        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header is not None
        assert set_cookie_header.split("; ") == [
            f"custom-csrftoken={csrf_token}",
            "Path=/",
            "SameSite=lax",
        ]

        response = client.post("/", headers={"x-custom-csrftoken": csrf_token})
        assert response.status_code == HTTP_201_CREATED


@pytest.mark.parametrize(
    "engine, template",
    (
        (JinjaTemplateEngine, "{{csrf_input}}"),
        (MakoTemplateEngine, "${csrf_input}"),
    ),
)
def test_csrf_form_parsing(engine: Any, template: str, tmp_path: Path) -> None:
    @get(path="/", media_type=MediaType.HTML)
    def handler() -> Template:
        return Template(template_name="abc.html")

    @post("/")
    def form_handler(data: dict = Body(media_type=RequestEncodingType.URL_ENCODED)) -> dict:
        return data

    with create_test_client(
        route_handlers=[handler, form_handler],
        template_config=TemplateConfig(
            directory=tmp_path,
            engine=engine,
        ),
        csrf_config=CSRFConfig(secret=str(urandom(10))),
    ) as client:
        url = f"{client.base_url!s}/"
        Path(tmp_path / "abc.html").write_text(
            f'<html><body><div><form action="{url}" method="post">{template}</form></div></body></html>'
        )
        _ = client.get("/")
        response = client.get("/")
        html_soup = BeautifulSoup(html.unescape(response.text), features="html.parser")
        data = {"_csrf_token": html_soup.body.div.form.input.attrs.get("value")}  # type: ignore[union-attr]
        response = client.post("/", data=data)
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == data


def test_csrf_middleware_exclude_from_check_via_opts() -> None:
    @post("/", exclude_from_csrf=True)
    def post_handler(data: dict = Body(media_type=RequestEncodingType.URL_ENCODED)) -> dict:
        return data

    with create_test_client(
        route_handlers=[post_handler],
        csrf_config=CSRFConfig(secret=str(urandom(10))),
    ) as client:
        data = {"field": "value"}
        response = client.post("/", data=data)
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == data


def test_csrf_middleware_exclude_from_check() -> None:
    @post("/protected-handler")
    def post_handler(data: dict = Body(media_type=RequestEncodingType.URL_ENCODED)) -> dict:
        return data

    @post("/unprotected-handler")
    def post_handler2(data: dict = Body(media_type=RequestEncodingType.URL_ENCODED)) -> dict:
        return data

    with create_test_client(
        route_handlers=[post_handler, post_handler2],
        csrf_config=CSRFConfig(secret=str(urandom(10)), exclude=["unprotected-handler"]),
    ) as client:
        data = {"field": "value"}
        response = client.post("/protected-handler", data=data)
        assert response.status_code == HTTP_403_FORBIDDEN

        response = client.post("/unprotected-handler", data=data)
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == data


def test_csrf_middleware_exclude_from_set_cookies() -> None:
    #  https://github.com/litestar-org/litestar/issues/3688
    #  middleware should be bypassed completely when excluded, so no cookies should be set

    @get("/protected-handler")
    def get_handler() -> dict:
        return {}

    @get("/unprotected-handler")
    def get_handler2() -> dict:
        return {}

    with create_test_client(
        route_handlers=[get_handler, get_handler2],
        csrf_config=CSRFConfig(secret=str(urandom(10)), exclude=["unprotected-handler"]),
    ) as client:
        response = client.get("/unprotected-handler")
        assert response.status_code == HTTP_200_OK
        assert "set-cookie" not in response.headers

        response = client.get("/protected-handler")
        assert response.status_code == HTTP_200_OK
        assert "set-cookie" in response.headers


def test_csrf_middleware_configure_name_for_exclude_from_check_via_opts() -> None:
    @post("/handler", exclude_from_csrf=True)
    def post_handler(data: dict = Body(media_type=RequestEncodingType.URL_ENCODED)) -> dict:
        return data

    @post("/handler2", custom_exclude_from_csrf=True)
    def post_handler2(data: dict = Body(media_type=RequestEncodingType.URL_ENCODED)) -> dict:
        return data

    with create_test_client(
        route_handlers=[post_handler, post_handler2],
        csrf_config=CSRFConfig(secret=str(urandom(10)), exclude_from_csrf_key="custom_exclude_from_csrf"),
    ) as client:
        data = {"field": "value"}
        response = client.post("/handler", data=data)
        assert response.status_code == HTTP_403_FORBIDDEN

        data = {"field": "value"}
        response = client.post("/handler2", data=data)
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == data
