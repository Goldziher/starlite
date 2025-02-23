from typing import Any
from urllib.parse import urlencode

import pytest

from litestar import HttpMethod
from litestar._parsers import (
    parse_cookie_string,
    parse_query_string,
    parse_url_encoded_form_data,
)
from litestar.datastructures import Cookie, MultiDict
from litestar.testing import RequestFactory, create_test_client


def test_parse_form_data() -> None:
    result = parse_url_encoded_form_data(
        encoded_data=urlencode(
            [
                ("value", "10"),
                ("value", "12"),
                ("veggies", '["tomato", "potato", "aubergine"]'),
                ("nested", '{"some_key": "some_value"}'),
                ("calories", "122.53"),
                ("healthy", "true"),
                ("polluting", "false"),
            ]
        ).encode(),
    )
    assert result == {
        "value": ["10", "12"],
        "veggies": '["tomato", "potato", "aubergine"]',
        "nested": '{"some_key": "some_value"}',
        "calories": "122.53",
        "healthy": "true",
        "polluting": "false",
    }


def test_parse_utf8_form_data() -> None:
    result = parse_url_encoded_form_data(
        encoded_data=urlencode(
            [
                ("value", "äüß"),
            ]
        ).encode(),
    )
    assert result == {"value": "äüß"}


@pytest.mark.parametrize(
    "cookie_string, expected",
    (
        ("ABC    = 123;   efg  =   456", {"ABC": "123", "efg": "456"}),
        ("foo= ; bar=", {"foo": "", "bar": ""}),
        ('foo="bar=123456789&name=moisheZuchmir"', {"foo": "bar=123456789&name=moisheZuchmir"}),
        ("email=%20%22%2c%3b%2f", {"email": ' ",;/'}),
        ("foo=%1;bar=bar", {"foo": "%1", "bar": "bar"}),
        ("foo=bar;fizz  ; buzz", {"": "buzz", "foo": "bar"}),
        ("  fizz; foo=  bar", {"": "fizz", "foo": "bar"}),
        ("foo=false;bar=bar;foo=true", {"bar": "bar", "foo": "true"}),
        ("foo=;bar=bar;foo=boo", {"bar": "bar", "foo": "boo"}),
        (
            Cookie(key="abc", value="123", path="/head", domain="localhost").to_header(header=""),
            {"Domain": "localhost", "Path": "/head", "SameSite": "lax", "abc": "123"},
        ),
    ),
)
def test_parse_cookie_string(cookie_string: str, expected: dict[str, str]) -> None:
    assert parse_cookie_string(cookie_string) == expected


def test_parse_query_string() -> None:
    query: dict[str, Any] = {
        "value": "10",
        "veggies": ["tomato", "potato", "aubergine"],
        "calories": "122.53",
        "healthy": True,
        "polluting": False,
    }
    request = RequestFactory().get(query_params=query)
    result = MultiDict(parse_query_string(request.scope.get("query_string", b"")))

    assert result.dict() == {
        "value": ["10"],
        "veggies": ["tomato", "potato", "aubergine"],
        "calories": ["122.53"],
        "healthy": ["True"],
        "polluting": ["False"],
    }


@pytest.mark.parametrize(
    "values",
    (
        (("first", "x@test.com"), ("second", "aaa")),
        (("first", "&@A.ac"), ("second", "aaa")),
        (("first", "a@A.ac&"), ("second", "aaa")),
        (("first", "a@A&.ac"), ("second", "aaa")),
    ),
)
def test_query_parsing_of_escaped_values(values: tuple[tuple[str, str], tuple[str, str]]) -> None:
    # https://github.com/litestar-org/litestar/issues/915
    with create_test_client([]) as client:
        request = client.build_request(method=HttpMethod.GET, url="http://www.example.com", params=dict(values))
        parsed_query = parse_query_string(request.url.query)
        assert parsed_query == values
