from collections.abc import Mapping
from itertools import permutations
from typing import TYPE_CHECKING, Optional

import pytest

from litestar import get, route
from litestar.config.cors import CORSConfig
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client
from tests.helpers import RANDOM

if TYPE_CHECKING:
    from litestar.types import Method


@pytest.mark.parametrize(
    "http_methods",
    (list(perm) for perm in iter(permutations(["GET", "POST", "PATCH", "DELETE", "HEAD"], r=RANDOM.randrange(1, 6)))),
)
def test_regular_options_request(http_methods: list["Method"]) -> None:
    @route("/", http_method=http_methods)
    def handler() -> None:
        return None

    with create_test_client(handler, openapi_config=None) as client:
        response = client.options("/")
        assert response.status_code == HTTP_204_NO_CONTENT, response.text
        assert response.headers.get("Allow") == ", ".join(sorted({*http_methods, "OPTIONS"}))


def test_cors_options_request_without_origin_passes() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(handler, cors_config=CORSConfig(allow_origins=["http://testserver.local"])) as client:
        response = client.options("/")
        assert response.status_code == HTTP_204_NO_CONTENT
        assert response.headers.get("Allow") == "GET, OPTIONS"


def test_cors_options_request_with_correct_origin_passes() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(handler, cors_config=CORSConfig(allow_origins=["http://testserver.local"])) as client:
        response = client.options("/", headers={"Origin": "http://testserver.local"})
        assert response.status_code == HTTP_204_NO_CONTENT
        assert response.headers.get("Access-Control-Allow-Methods") == "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
        assert response.headers.get("Access-Control-Allow-Origin") == "http://testserver.local"
        assert response.headers.get("Vary") == "Origin"


def test_cors_options_request_with_correct_origin_passes_with_allow_all_origins() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(handler, cors_config=CORSConfig(allow_origins=["*"])) as client:
        response = client.options("/", headers={"Origin": "http://testserver.local"})
        assert response.status_code == HTTP_204_NO_CONTENT
        assert response.headers.get("Access-Control-Allow-Methods") == "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
        assert "Vary" not in response.headers


def test_cors_options_request_with_wrong_origin_fails() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(handler, cors_config=CORSConfig(allow_origins=["http://testserver.local"])) as client:
        response = client.options("/", headers={"Origin": "https://moishe.zuchmir"})
        assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "allowed_origins, allowed_origin_regex, origin",
    (
        (["http://testserver.local", "https://moishe.zuchmir"], None, "https://moishe.zuchmir"),
        (["http://testserver.local", "https://moishe.zuchmir"], None, "http://testserver.local"),
        (["http://testserver.local", "https://moishe.*"], None, "https://moishe.zuchmir"),
        (["http://testserver.local", "https://moishe.*.abc.com"], None, "https://moishe.zuchmir.abc.com"),
        (["http://testserver.local", "https://moishe.*.*.com"], None, "https://moishe.zuchmir.zzz.com"),
        (["http://testserver.local"], "https://moishe.*.*.com", "https://moishe.zuchmir.zzz.com"),
        ([], "https://moishe.*.*.com", "https://moishe.zuchmir.zzz.com"),
    ),
)
def test_cors_options_request_with_different_domains_matches_regex(
    allowed_origins: list[str], allowed_origin_regex: Optional[str], origin: str
) -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(
        handler, cors_config=CORSConfig(allow_origins=allowed_origins, allow_origin_regex=allowed_origin_regex)
    ) as client:
        response = client.options("/", headers={"Origin": origin})
        assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.parametrize(
    "origin, allow_credentials",
    (("http://testserver.local", False), ("http://testserver.local", True), (None, False), (None, True)),
)
def test_cors_options_request_allow_credentials_header(origin: str, allow_credentials: bool) -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(
        handler, cors_config=CORSConfig(allow_origins=["http://testserver.local"], allow_credentials=allow_credentials)
    ) as client:
        headers: Mapping[str, str] = {"Origin": origin} if origin else {}
        response = client.options("/", headers=headers)
        assert response.status_code == HTTP_204_NO_CONTENT

        if origin and allow_credentials:
            assert response.headers.get("Access-Control-Allow-Credentials") == str(allow_credentials).lower()
        else:
            assert "Access-Control-Allow-Credentials" not in response.headers


def test_cors_options_request_with_wrong_headers_fails() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(handler, cors_config=CORSConfig(allow_headers=["X-My-Header"])) as client:
        response = client.options(
            "/",
            headers={
                "Origin": "http://testserver.local",
                "Access-Control-Request-Headers": "X-My-Header, X-Another-Header",
            },
        )
        assert response.status_code == HTTP_400_BAD_REQUEST


def test_cors_options_request_with_correct_headers_passes() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(
        handler, cors_config=CORSConfig(allow_headers=["X-My-Header", "X-Another-Header"])
    ) as client:
        response = client.options(
            "/",
            headers={
                "Origin": "http://testserver.local",
                "Access-Control-Request-Headers": "X-My-Header, X-Another-Header",
            },
        )
        assert response.status_code == HTTP_204_NO_CONTENT


def test_requested_headers_are_reflected_back_when_allow_all_headers() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(handler, cors_config=CORSConfig(allow_headers=["*"])) as client:
        response = client.options(
            "/",
            headers={
                "Origin": "http://testserver.local",
                "Access-Control-Request-Headers": "X-My-Header, X-Another-Header",
            },
        )
        assert response.status_code == HTTP_204_NO_CONTENT
        assert (
            response.headers.get("Access-Control-Allow-Headers")
            == "Accept, Accept-Language, Content-Language, Content-Type, X-Another-Header, X-My-Header"
        )


def test_cors_options_request_fails_if_request_method_not_allowed() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(handler, cors_config=CORSConfig(allow_methods=["GET"])) as client:
        response = client.options(
            "/",
            headers={"Origin": "http://testserver.local", "Access-Control-Request-Method": "POST"},
        )
        assert response.status_code == HTTP_400_BAD_REQUEST


def test_cors_options_request_succeeds_if_request_method_not_specified() -> None:
    @get("/")
    def handler() -> None:
        return None

    with create_test_client(handler, cors_config=CORSConfig(allow_methods=["GET"])) as client:
        response = client.options(
            "/",
            headers={
                "Origin": "http://testserver.local",
            },
        )
        assert response.status_code == HTTP_204_NO_CONTENT
        assert response.headers.get("Access-Control-Allow-Methods") == "GET"
