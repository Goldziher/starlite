from pathlib import Path
from typing import Any

import pytest

from litestar import get
from litestar.contrib.htmx._utils import HTMXHeaders
from litestar.contrib.htmx.request import HTMXRequest
from litestar.contrib.htmx.response import (
    ClientRedirect,
    ClientRefresh,
    HTMXTemplate,
    HXLocation,
    HXStopPolling,
    PushUrl,
    ReplaceUrl,
    Reswap,
    Retarget,
    TriggerEvent,
)
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.contrib.mako import MakoTemplateEngine
from litestar.status_codes import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.template.config import TemplateConfig
from litestar.testing import create_test_client


async def test_hx_stop_polling_response() -> None:
    @get("/")
    def handler() -> HXStopPolling:
        return HXStopPolling()

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == 286


async def test_client_redirect_response() -> None:
    @get("/")
    def handler() -> ClientRedirect:
        return ClientRedirect(redirect_to="https://example.com")

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers.get(HTMXHeaders.REDIRECT) == "https://example.com"
        assert response.headers.get("location") is None


async def test_client_refresh_response() -> None:
    @get("/")
    def handler() -> ClientRefresh:
        return ClientRefresh()

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers[HTMXHeaders.REFRESH] == "true"


async def test_push_url_false_response() -> None:
    @get("/")
    def handler() -> PushUrl:
        return PushUrl(content="Success!", push_url=False)

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers[HTMXHeaders.PUSH_URL] == "false"


async def test_push_url_response() -> None:
    @get("/")
    def handler() -> PushUrl:
        return PushUrl(content="Success!", push_url="/index.html")

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Success!"
        assert response.headers[HTMXHeaders.PUSH_URL] == "/index.html"


async def test_replace_url_false_response() -> None:
    @get("/")
    def handler() -> ReplaceUrl:
        return ReplaceUrl(content="Success!", replace_url=False)

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers[HTMXHeaders.REPLACE_URL] == "false"


async def test_replace_url_response() -> None:
    @get("/")
    def handler() -> ReplaceUrl:
        return ReplaceUrl(content="Success!", replace_url="/index.html")

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Success!"
        assert response.headers[HTMXHeaders.REPLACE_URL] == "/index.html"


async def test_reswap_response() -> None:
    @get("/")
    def handler() -> Reswap:
        return Reswap(content="Success!", method="beforebegin")

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Success!"
        assert response.headers[HTMXHeaders.RE_SWAP] == "beforebegin"


async def test_retarget_response() -> None:
    @get("/")
    def handler() -> Retarget:
        return Retarget(content="Success!", target="#element")

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Success!"
        assert response.headers[HTMXHeaders.RE_TARGET] == "#element"


async def test_trigger_event_response_success() -> None:
    @get("/")
    def handler() -> TriggerEvent:
        return TriggerEvent(
            content="Success!", name="alert", after="receive", params={"warning": "Confirm your choice!"}
        )

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Success!"
        assert response.headers[HTMXHeaders.TRIGGER_EVENT] == '{"alert":{"warning":"Confirm your choice!"}}'


async def test_trigger_event_response_no_params() -> None:
    @get("/")
    def handler() -> TriggerEvent:
        return TriggerEvent(content="Success!", name="alert", after="receive")

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")

        assert response.status_code == HTTP_200_OK
        assert response.text == "Success!"
        assert response.headers[HTMXHeaders.TRIGGER_EVENT] == '{"alert":{}}'


async def test_trigger_event_response_after_settle() -> None:
    @get("/")
    def handler() -> TriggerEvent:
        return TriggerEvent(
            content="Success!", name="alert", after="settle", params={"warning": "Confirm your choice!"}
        )

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Success!"
        assert response.headers[HTMXHeaders.TRIGGER_AFTER_SETTLE] == '{"alert":{"warning":"Confirm your choice!"}}'


async def test_trigger_event_response_after_swap() -> None:
    @get("/")
    def handler() -> TriggerEvent:
        return TriggerEvent(content="Success!", name="alert", after="swap", params={"warning": "Confirm your choice!"})

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Success!"
        assert response.headers[HTMXHeaders.TRIGGER_AFTER_SWAP] == '{"alert":{"warning":"Confirm your choice!"}}'


async def test_trigger_event_response_invalid_after() -> None:
    @get("/")
    def handler() -> TriggerEvent:
        return TriggerEvent(
            content="Success!",
            name="alert",
            after="invalid",  # type: ignore[arg-type]
            params={"warning": "Confirm your choice!"},
        )

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR


async def test_hx_location_response_success() -> None:
    @get("/")
    def handler() -> HXLocation:
        return HXLocation(redirect_to="/contact-us")

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        spec = response.headers[HTMXHeaders.LOCATION]
        assert response.status_code == HTTP_200_OK
        assert "Location" not in response.headers
        assert spec == '{"path":"/contact-us"}'


async def test_hx_location_response_with_all_parameters() -> None:
    @get("/")
    def handler() -> HXLocation:
        return HXLocation(
            redirect_to="/contact-us",
            source="#button",
            event="click",
            target="#content",
            swap="innerHTML",
            hx_headers={"attribute": "value"},
            values={"action": "true"},
        )

    with create_test_client(route_handlers=[handler], request_class=HTMXRequest) as client:
        response = client.get("/")
        spec = response.headers[HTMXHeaders.LOCATION]
        assert response.status_code == HTTP_200_OK
        assert "Location" not in response.headers
        assert spec == (
            '{"path":"/contact-us","source":"#button","event":"click","target":"#content","swap":"innerHTML",'
            '"values":{"action":"true"},"hx_headers":{"attribute":"value"}}'
        )


@pytest.mark.parametrize(
    "engine, template, expected",
    (
        (
            JinjaTemplateEngine,
            "path: {{ request.scope['path'] }} custom_key: {{ custom_key }}",
            "path: / custom_key: custom_value",
        ),
        (
            MakoTemplateEngine,
            "path: ${request.scope['path']} custom_key: ${custom_key}",
            "path: / custom_key: custom_value",
        ),
    ),
)
def test_HTMXTemplate_response_success(engine: Any, template: str, expected: str, tmp_path: Path) -> None:
    Path(tmp_path / "abc.html").write_text(template)

    @get(path="/")
    def handler() -> HTMXTemplate:
        return HTMXTemplate(
            template_name="abc.html",
            context={"request": {"scope": {"path": "nope"}}, "custom_key": "custom_value"},
            push_url="/about",
            re_swap="beforebegin",
            re_target="#new-target-id",
            trigger_event="showMessage",
            params={"alert": "Confirm your Choice."},
            after="receive",
        )

    with create_test_client(
        route_handlers=[handler],
        template_config=TemplateConfig(
            directory=tmp_path,
            engine=engine,
        ),
    ) as client:
        response = client.get("/")
        assert response.text == expected
        assert response.headers.get(HTMXHeaders.PUSH_URL) == "/about"
        assert response.headers.get(HTMXHeaders.RE_SWAP) == "beforebegin"
        assert response.headers.get(HTMXHeaders.RE_TARGET) == "#new-target-id"
        assert response.headers.get(HTMXHeaders.TRIGGER_EVENT) == '{"showMessage":{"alert":"Confirm your Choice."}}'


@pytest.mark.parametrize(
    "engine, template, expected",
    (
        (JinjaTemplateEngine, "path: {{ request.scope['path'] }}", "path: /"),
        (MakoTemplateEngine, "path: ${request.scope['path']}", "path: /"),
    ),
)
def test_HTMXTemplate_response_no_params(engine: Any, template: str, expected: str, tmp_path: Path) -> None:
    Path(tmp_path / "abc.html").write_text(template)

    @get(path="/")
    def handler() -> HTMXTemplate:
        return HTMXTemplate(
            template_name="abc.html",
            context={"request": {"scope": {"path": "nope"}}},
        )

    with create_test_client(
        route_handlers=[handler],
        template_config=TemplateConfig(
            directory=tmp_path,
            engine=engine,
        ),
    ) as client:
        response = client.get("/")
        assert response.text == expected
        assert response.headers.get(HTMXHeaders.PUSH_URL) is None
        assert response.headers.get(HTMXHeaders.RE_SWAP) is None
        assert response.headers.get(HTMXHeaders.RE_TARGET) is None
        assert response.headers.get(HTMXHeaders.TRIGGER_EVENT) is None


@pytest.mark.parametrize(
    "engine, template, expected",
    (
        (JinjaTemplateEngine, "path: {{ request.scope['path'] }}", "path: /"),
        (MakoTemplateEngine, "path: ${request.scope['path']}", "path: /"),
    ),
)
def test_HTMXTemplate_response_push_url_set_to_false(engine: Any, template: str, expected: str, tmp_path: Path) -> None:
    Path(tmp_path / "abc.html").write_text(template)

    @get(path="/")
    def handler() -> HTMXTemplate:
        return HTMXTemplate(
            template_name="abc.html",
            context={"request": {"scope": {"path": "nope"}}},
            push_url=False,
        )

    with create_test_client(
        route_handlers=[handler],
        template_config=TemplateConfig(
            directory=tmp_path,
            engine=engine,
        ),
    ) as client:
        response = client.get("/")
        assert response.text == expected
        assert response.headers.get(HTMXHeaders.PUSH_URL) == "false"
        assert response.headers.get(HTMXHeaders.RE_SWAP) is None
        assert response.headers.get(HTMXHeaders.RE_TARGET) is None
        assert response.headers.get(HTMXHeaders.TRIGGER_EVENT) is None


@pytest.mark.parametrize(
    "engine, template, expected",
    (
        (JinjaTemplateEngine, "path: {{ request.scope['path'] }}", "path: /"),
        (MakoTemplateEngine, "path: ${request.scope['path']}", "path: /"),
    ),
)
def test_htmx_template_response_bad_trigger_params(engine: Any, template: str, expected: str, tmp_path: Path) -> None:
    Path(tmp_path / "abc.html").write_text(template)

    @get(path="/")
    def handler() -> HTMXTemplate:
        return HTMXTemplate(
            template_name="abc.html",
            context={"request": {"scope": {"path": "nope"}}},
            trigger_event="showMessage",
            params={"alert": "Confirm your Choice."},
            after="begin",  # type: ignore[arg-type]
        )

    with create_test_client(
        route_handlers=[handler],
        template_config=TemplateConfig(
            directory=tmp_path,
            engine=engine,
        ),
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert response.headers.get(HTMXHeaders.PUSH_URL) is None
        assert response.headers.get(HTMXHeaders.RE_SWAP) is None
        assert response.headers.get(HTMXHeaders.RE_TARGET) is None
        assert response.headers.get(HTMXHeaders.TRIGGER_EVENT) is None
