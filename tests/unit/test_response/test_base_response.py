from pathlib import PurePosixPath
from typing import Any, Optional

import pytest

from litestar import MediaType, get
from litestar.datastructures import Cookie
from litestar.exceptions import ImproperlyConfiguredException
from litestar.response import Response
from litestar.response.base import ASGIResponse
from litestar.serialization import default_serializer, get_serializer
from litestar.status_codes import (
    HTTP_100_CONTINUE,
    HTTP_101_SWITCHING_PROTOCOLS,
    HTTP_102_PROCESSING,
    HTTP_103_EARLY_HINTS,
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_304_NOT_MODIFIED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from litestar.testing import create_test_client
from litestar.types import Empty


def test_response_headers() -> None:
    @get("/")
    def handler() -> Response:
        return Response(content="hello world", media_type=MediaType.TEXT, headers={"first": "123", "second": "456"})

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.headers["first"] == "123"
        assert response.headers["second"] == "456"
        assert response.headers["content-length"] == "11"
        assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_response_headers_do_not_lowercase_values() -> None:
    # reproduces: https://github.com/litestar-org/litestar/issues/693

    @get("/")
    def handler() -> Response:
        return Response(content="hello world", media_type=MediaType.TEXT, headers={"foo": "BaR"})

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.headers["foo"] == "BaR"


@pytest.mark.parametrize("as_instance", [True, False])
def test_set_cookie(as_instance: bool) -> None:
    @get("/")
    def handler() -> Response:
        response = Response(content=None)
        if as_instance:
            response.set_cookie(Cookie(key="test", value="abc", max_age=60, expires=60, secure=True, httponly=True))
        else:
            response.set_cookie(key="test", value="abc", max_age=60, expires=60, secure=True, httponly=True)
        assert len(response.cookies) == 1
        return response

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.cookies.get("test") == "abc"


def test_delete_cookie() -> None:
    @get("/create")
    def create_cookie_handler() -> Response:
        response = Response(content=None)
        response.set_cookie("test", "abc", max_age=60, expires=60, secure=True, httponly=True)
        assert len(response.cookies) == 1
        return response

    @get("/delete")
    def delete_cookie_handler() -> Response:
        response = Response(content=None)
        response.delete_cookie(
            "test",
            "abc",
        )
        assert len(response.cookies) == 1
        return response

    with create_test_client(route_handlers=[create_cookie_handler, delete_cookie_handler]) as client:
        response = client.get("/create")
        assert response.cookies.get("test") == "abc"
        assert client.cookies.get("test") == "abc"
        response = client.get("/delete")
        assert response.cookies.get("test") is None
        # the commented out assert fails, because of the starlette test client's behaviour - which doesn't clear
        # cookies.


@pytest.mark.parametrize(
    "media_type, expected, should_have_content_length",
    ((MediaType.TEXT, b"", False), (MediaType.HTML, b"", False), (MediaType.JSON, b"null", True)),
)
def test_empty_response(media_type: MediaType, expected: bytes, should_have_content_length: bool) -> None:
    @get("/", media_type=media_type)
    def handler() -> None:
        return

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.content == expected
        assert response.headers["content-length"] == str(len(expected))


@pytest.mark.parametrize("status_code", (HTTP_204_NO_CONTENT, HTTP_304_NOT_MODIFIED))
def test_response_without_payload(status_code: int) -> None:
    @get("/")
    def handler() -> Response:
        return Response(b"", status_code=status_code)

    with create_test_client(handler) as client:
        response = client.get("/")

        assert "content-type" not in response.headers
        assert "content-length" not in response.headers


@pytest.mark.parametrize(
    "status, body, should_raise",
    (
        (HTTP_100_CONTINUE, None, False),
        (HTTP_101_SWITCHING_PROTOCOLS, None, False),
        (HTTP_102_PROCESSING, None, False),
        (HTTP_103_EARLY_HINTS, None, False),
        (HTTP_204_NO_CONTENT, None, False),
        (HTTP_100_CONTINUE, "1", True),
        (HTTP_101_SWITCHING_PROTOCOLS, "1", True),
        (HTTP_102_PROCESSING, "1", True),
        (HTTP_103_EARLY_HINTS, "1", True),
        (HTTP_204_NO_CONTENT, "1", True),
    ),
)
def test_statuses_without_body(status: int, body: Optional[str], should_raise: bool) -> None:
    @get("/")
    def handler() -> Response:
        return Response(content=body, status_code=status)

    with create_test_client(handler) as client:
        response = client.get("/")
        if should_raise:
            assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        else:
            assert response.status_code == status
            assert "content-length" not in response.headers


@pytest.mark.parametrize(
    "body, media_type, should_raise",
    (
        ("", MediaType.TEXT, False),
        ("abc", MediaType.TEXT, False),
        (b"", MediaType.HTML, False),
        (b"abc", MediaType.HTML, False),
        ({"key": "value"}, MediaType.TEXT, True),
        ([1, 2, 3], MediaType.TEXT, True),
        ({"key": "value"}, MediaType.HTML, True),
        ([1, 2, 3], MediaType.HTML, True),
        ([], MediaType.HTML, False),
        ([], MediaType.TEXT, False),
        ({}, MediaType.HTML, False),
        ({}, MediaType.TEXT, False),
        ({"abc": "def"}, MediaType.JSON, False),
        (Empty, MediaType.JSON, True),
        ({"key": "value"}, "application/something+json", False),
    ),
)
def test_render_method(body: Any, media_type: str, should_raise: bool) -> None:
    @get("/", media_type=media_type)
    def handler() -> Any:
        return body

    with create_test_client(handler) as client:
        response = client.get("/")
        if should_raise:
            assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        else:
            assert response.status_code == HTTP_200_OK


def test_get_serializer() -> None:
    class Foo:
        pass

    foo_encoder = {Foo: lambda f: "it's a foo"}
    path_encoder = {PurePosixPath: lambda p: "it's a path"}

    class FooResponse(Response):
        type_encoders = foo_encoder

    assert get_serializer() is default_serializer

    assert get_serializer(type_encoders=foo_encoder)(Foo()) == "it's a foo"
    assert get_serializer(type_encoders=path_encoder)(PurePosixPath()) == "it's a path"

    assert get_serializer(FooResponse(None).type_encoders)(Foo()) == "it's a foo"
    assert (
        get_serializer(FooResponse(None, type_encoders={Foo: lambda f: "foo"}).response_type_encoders)(Foo()) == "foo"
    )


def test_head_response_doesnt_support_content() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        ASGIResponse(body=b"hello world", media_type=MediaType.TEXT, is_head_response=True)


def test_asgi_response_encoded_headers() -> None:
    response = ASGIResponse(encoded_headers=[(b"foo", b"bar")])
    assert response.encode_headers() == [
        (b"foo", b"bar"),
        (b"content-type", b"application/json"),
        (b"content-length", b"0"),
    ]
