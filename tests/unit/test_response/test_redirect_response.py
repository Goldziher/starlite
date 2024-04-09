"""A large part of the tests in this file were adapted from:

https://github.com/encode/starlette/blob/master/tests/test_responses.py And are meant to ensure our compatibility with
their API.
"""

from typing import TYPE_CHECKING, Optional

import pytest

from litestar import get
from litestar.exceptions import ImproperlyConfiguredException
from litestar.response.base import ASGIResponse
from litestar.response.redirect import ASGIRedirectResponse, Redirect
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient, create_test_client

if TYPE_CHECKING:
    from litestar.types import Receive, Scope, Send


def test_redirect_response() -> None:
    async def app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["path"] == "/":
            response = ASGIResponse(body=b"hello, world", media_type="text/plain")
        else:
            response = ASGIRedirectResponse(path="/")
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/redirect")
    assert response.text == "hello, world"
    assert response.url == "http://testserver.local/"


def test_quoting_redirect_response() -> None:
    async def app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["path"] == "/test/":
            response = ASGIResponse(body=b"hello, world", media_type="text/plain")
        else:
            response = ASGIRedirectResponse(path="/test/")
        await response(scope, receive, send)

    client = TestClient(app)
    response = client.get("/redirect", follow_redirects=True)
    assert response.text == "hello, world"
    assert str(response.url) == "http://testserver.local/test/"


def test_redirect_response_content_length_header() -> None:
    async def app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["path"] == "/":
            response = ASGIResponse(body=b"hello", media_type="text/plain")
        else:
            response = ASGIRedirectResponse(path="/")
        await response(scope, receive, send)

    client: TestClient = TestClient(app)
    response = client.request("GET", "/redirect", follow_redirects=False)
    assert str(response.url) == "http://testserver.local/redirect"
    assert "content-length" in response.headers


def test_redirect_response_status_validation() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        ASGIRedirectResponse(path="/", status_code=HTTP_200_OK)  # type:ignore[arg-type]


def test_redirect_response_html_media_type() -> None:
    async def app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["path"] == "/":
            response = ASGIResponse(body=b"hello")
        else:
            response = ASGIRedirectResponse(path="/", media_type="text/html")
        await response(scope, receive, send)

    client: TestClient = TestClient(app)
    response = client.request("GET", "/redirect", follow_redirects=False)
    assert str(response.url) == "http://testserver.local/redirect"
    assert "text/html" in str(response.headers["Content-Type"])


def test_redirect_response_media_type_validation() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        ASGIRedirectResponse(path="/", media_type="application/mspgpack")


@pytest.mark.parametrize(
    "status_code,expected_status_code",
    [
        (301, 301),
        (302, 302),
        (303, 303),
        (307, 307),
        (308, 308),
    ],
)
def test_redirect_dynamic_status_code(status_code: Optional[int], expected_status_code: int) -> None:
    @get("/")
    def handler() -> Redirect:
        return Redirect(path="/something-else", status_code=status_code)  # type: ignore[arg-type]

    with create_test_client(
        [handler],
    ) as client:
        res = client.get("/", follow_redirects=False)
        assert res.status_code == expected_status_code


@pytest.mark.parametrize("handler_status_code", [301, 307, None])
def test_redirect(handler_status_code: Optional[int]) -> None:
    @get("/", status_code=handler_status_code)
    def handler() -> Redirect:
        return Redirect(path="/something-else", status_code=handler_status_code)  # type: ignore[arg-type]

    with create_test_client([handler]) as client:
        res = client.get("/", follow_redirects=False)
        assert res.status_code == 302 if handler_status_code is None else handler_status_code
