from typing import Any, Optional

import pytest

from litestar import MediaType, get
from litestar.contrib.htmx.request import HTMXRequest
from litestar.plugins.htmx import HTMXHeaders
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client

pytestmark = pytest.mark.anyio


def test_health_check() -> None:
    @get("/health-check", media_type=MediaType.TEXT)
    def health_check() -> str:
        return "healthy"

    with create_test_client(route_handlers=health_check) as client:
        response = client.get("/health-check")
        assert response.status_code == HTTP_200_OK
        assert response.text == "healthy"


async def test_bool_default() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> bool:
        return bool(request.htmx)

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "false"


async def test_bool_false() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> bool:
        return bool(request.htmx)

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.REQUEST.value: "false"})
        assert response.text == "false"


async def test_bool_true() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> bool:
        return bool(request.htmx)

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.REQUEST.value: "true"})
        assert response.text == "true"


async def test_boosted_default() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> bool:
        return request.htmx.boosted

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "false"


async def test_boosted_set() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> bool:
        return request.htmx.boosted

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.BOOSTED.value: "true"})
        assert response.text == "true"


def test_current_url_default() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.current_url is None
        return request.htmx.current_url

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "null"


def test_current_url_set() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.current_url == "https://example.com"
        return request.htmx.current_url

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.CURRENT_URL.value: "https://example.com"})
        assert response.text == "https://example.com"


def test_current_url_set_url_encoded() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        return request.htmx.current_url

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get(
            "/",
            headers={
                HTMXHeaders.CURRENT_URL.value: "https%3A%2F%2Fexample.com%2F%3F",
                f"{HTMXHeaders.CURRENT_URL.value}-URI-AutoEncoded": "true",
            },
        )
        assert response.text == "https://example.com/?"


def test_current_url_abs_path_default() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.current_url_abs_path is None
        return request.htmx.current_url_abs_path

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "null"


def test_current_url_abs_path_set() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.current_url_abs_path == "/duck/?quack=true#h2"
        return request.htmx.current_url_abs_path

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get(
            "/", headers={HTMXHeaders.CURRENT_URL.value: "http://testserver.local/duck/?quack=true#h2"}
        )
        assert response.text == "/duck/?quack=true#h2"


def test_current_url_abs_path_set_other_domain() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.current_url_abs_path is None
        return request.htmx.current_url_abs_path

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.CURRENT_URL.value: "http://example.com/duck/?quack=true#h2"})
        assert response.text == "null"


def test_history_restore_request_false() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> bool:
        assert request.htmx.history_restore_request is False
        return request.htmx.history_restore_request

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.HISTORY_RESTORE_REQUEST.value: "false"})
        assert response.text == "false"


def test_history_restore_request_true() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> bool:
        assert request.htmx.history_restore_request is True
        return request.htmx.history_restore_request

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.HISTORY_RESTORE_REQUEST.value: "true"})
        assert response.text == "true"


def test_prompt_default() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.prompt is None
        return request.htmx.prompt

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "null"


def test_prompt_set() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.prompt == "Yes"
        return request.htmx.prompt

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.PROMPT.value: "Yes"})
        assert response.text == "Yes"


def test_target_default() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.target is None
        return request.htmx.target

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "null"


def test_target_set() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.target == "#element"
        return request.htmx.target

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.TARGET.value: "#element"})
        assert response.text == "#element"


def test_trigger_default() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.trigger is None
        return request.htmx.trigger

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "null"


def test_trigger_set() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.trigger == "#element"
        return request.htmx.trigger

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.TRIGGER_ID.value: "#element"})
        assert response.text == "#element"


def test_trigger_name_default() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.trigger_name is None
        return request.htmx.trigger_name

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "null"


def test_trigger_name_set() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Optional[str]:
        assert request.htmx.trigger_name == "name_of_element"
        return request.htmx.trigger_name

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.TRIGGER_NAME.value: "name_of_element"})
        assert response.text == "name_of_element"


def test_triggering_event_none() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> None:
        assert request.htmx.triggering_event is None
        return request.htmx.triggering_event

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.text == "null"


def test_triggering_event_bad_json() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> None:
        assert request.htmx.triggering_event is None
        return request.htmx.triggering_event

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/", headers={HTMXHeaders.TRIGGERING_EVENT.value: "{"})
        assert response.text == "null"


def test_triggering_event_good_json() -> None:
    @get("/")
    def handler(request: HTMXRequest) -> Any:
        return request.htmx.triggering_event

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get(
            "/",
            headers={
                HTMXHeaders.TRIGGERING_EVENT.value: "%7B%22target%22%3A%20null%7D",
                f"{HTMXHeaders.TRIGGERING_EVENT.value}-uri-autoencoded": "true",
            },
        )
        assert response.text == '{"target":null}'
