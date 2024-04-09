from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, List, Optional, Union

import pytest
from pytest import FixtureRequest

from litestar import MediaType
from litestar.datastructures import (
    Accept,
    CacheControlHeader,
    ETag,
    Headers,
    MutableScopeHeaders,
)
from litestar.datastructures.headers import Header
from litestar.exceptions import ImproperlyConfiguredException, ValidationException
from litestar.types.asgi_types import HTTPResponseBodyEvent, HTTPResponseStartEvent
from litestar.utils.dataclass import simple_asdict

if TYPE_CHECKING:
    from litestar.types.asgi_types import RawHeaders, RawHeadersList, Scope


@pytest.fixture
def raw_headers() -> "RawHeadersList":
    return [(b"foo", b"bar")]


@pytest.fixture
def raw_headers_tuple() -> "RawHeaders":
    return [(b"foo", b"bar")]


def test_header_container_requires_header_key_being_defined() -> None:
    class TestHeader(Header):
        def _get_header_value(self) -> str:
            return ""

        def from_header(self, header_value: str) -> "Header":  # type: ignore[explicit-override, override]
            return self

    with pytest.raises(ImproperlyConfiguredException):
        TestHeader().to_header()


@pytest.fixture
def mutable_headers(raw_headers: "RawHeadersList") -> MutableScopeHeaders:
    return MutableScopeHeaders({"headers": raw_headers})


@pytest.fixture
def mutable_headers_from_tuple(raw_headers_tuple: "RawHeaders") -> MutableScopeHeaders:
    return MutableScopeHeaders({"headers": raw_headers_tuple})


@pytest.fixture(params=[True, False])
def existing_headers_key(request: FixtureRequest) -> str:
    return "Foo" if request.param else "foo"


def test_headers_from_mapping() -> None:
    headers = Headers({"foo": "bar", "baz": "zab"})
    assert headers["foo"] == "bar"
    assert headers["baz"] == "zab"


def test_headers_from_raw_list() -> None:
    headers = Headers([(b"foo", b"bar"), (b"foo", b"baz")])
    assert headers.getall("foo") == ["bar", "baz"]


def test_headers_from_raw_tuple() -> None:
    headers = Headers(((b"foo", b"bar"), (b"foo", b"baz")))
    assert headers.getall("foo") == ["bar", "baz"]


def test_headers_from_scope(create_scope: "Callable[..., Scope]") -> None:
    headers = Headers.from_scope(create_scope(headers=[(b"foo", b"bar"), (b"buzz", b"bup")]))
    assert headers["foo"] == "bar"
    assert headers["buzz"] == "bup"


def test_headers_to_header_list() -> None:
    raw = [(b"foo", b"bar"), (b"foo", b"baz")]
    headers = Headers(raw)
    assert headers.to_header_list() == raw


def test_headers_tuple_to_header_list() -> None:
    raw = ((b"foo", b"bar"), (b"foo", b"baz"))
    headers = Headers(raw)
    assert headers.to_header_list() == list(raw)


def test_mutable_scope_headers_from_iterable() -> None:
    raw = [(b"foo", b"bar"), (b"foo", b"baz")]
    headers = MutableScopeHeaders({"headers": iter(raw)})
    assert headers.headers == raw


def test_mutable_scope_headers_from_message(raw_headers: "RawHeadersList", raw_headers_tuple: "RawHeaders") -> None:
    headers = MutableScopeHeaders.from_message(
        HTTPResponseStartEvent(type="http.response.start", status=200, headers=raw_headers)
    )
    assert headers.headers == raw_headers

    headers = MutableScopeHeaders.from_message(
        HTTPResponseStartEvent(type="http.response.start", status=200, headers=raw_headers_tuple)
    )
    assert headers.headers == list(raw_headers_tuple)


def test_mutable_scope_headers_from_message_invalid_type() -> None:
    with pytest.raises(ValueError):
        MutableScopeHeaders.from_message(HTTPResponseBodyEvent(type="http.response.body", body=b"", more_body=False))


def test_mutable_scope_headers_add(
    raw_headers: "RawHeadersList", mutable_headers: MutableScopeHeaders, existing_headers_key: str
) -> None:
    mutable_headers.add(existing_headers_key, "baz")
    assert raw_headers == [(b"foo", b"bar"), (b"foo", b"baz")]


def test_mutable_scope_headers_from_tuple_add(
    raw_headers_tuple: "RawHeaders", mutable_headers_from_tuple: MutableScopeHeaders, existing_headers_key: str
) -> None:
    mutable_headers_from_tuple.add(existing_headers_key, "baz")
    assert list(raw_headers_tuple) == [(b"foo", b"bar"), (b"foo", b"baz")]


def test_mutable_scope_headers_getall_singular_value(
    mutable_headers: MutableScopeHeaders, mutable_headers_from_tuple: MutableScopeHeaders, existing_headers_key: str
) -> None:
    assert mutable_headers.getall(existing_headers_key) == ["bar"]
    assert mutable_headers_from_tuple.getall(existing_headers_key) == ["bar"]


def test_mutable_scope_headers_getall_multi_value(
    mutable_headers: MutableScopeHeaders, mutable_headers_from_tuple: MutableScopeHeaders, existing_headers_key: str
) -> None:
    mutable_headers.add(existing_headers_key, "baz")
    assert mutable_headers.getall("foo") == ["bar", "baz"]

    mutable_headers_from_tuple.add(existing_headers_key, "baz")
    assert mutable_headers.getall("foo") == ["bar", "baz"]


def test_mutable_scope_headers_getall_not_found_no_default(mutable_headers: MutableScopeHeaders) -> None:
    with pytest.raises(KeyError):
        mutable_headers.getall("bar")


def test_mutable_scope_headers_getall_not_found_default(mutable_headers: MutableScopeHeaders) -> None:
    assert mutable_headers.getall("bar", ["default"]) == ["default"]


def test_mutable_scope_headers_extend_header_value(
    raw_headers: "RawHeadersList", mutable_headers: MutableScopeHeaders
) -> None:
    mutable_headers.extend_header_value("foo", "baz")
    assert raw_headers == [(b"foo", b"bar,baz")]


def test_mutable_scope_headers_from_tuple_extend_header_value(
    raw_headers_tuple: "RawHeaders", mutable_headers_from_tuple: MutableScopeHeaders
) -> None:
    mutable_headers_from_tuple.extend_header_value("foo", "baz")
    assert list(raw_headers_tuple) == [(b"foo", b"bar,baz")]


def test_mutable_scope_headers_extend_header_value_new_header(
    raw_headers: "RawHeadersList", mutable_headers: MutableScopeHeaders
) -> None:
    mutable_headers.extend_header_value("bar", "baz")
    assert raw_headers == [(b"foo", b"bar"), (b"bar", b"baz")]


def test_mutable_scope_headers_from_tuple_extend_header_value_new_header(
    raw_headers_tuple: "RawHeaders", mutable_headers_from_tuple: MutableScopeHeaders
) -> None:
    mutable_headers_from_tuple.extend_header_value("bar", "baz")
    assert list(raw_headers_tuple) == [(b"foo", b"bar"), (b"bar", b"baz")]


def test_mutable_scope_headers_getitem(mutable_headers: MutableScopeHeaders, existing_headers_key: str) -> None:
    assert mutable_headers[existing_headers_key] == "bar"


def test_mutable_scope_headers_getitem_not_found(mutable_headers: MutableScopeHeaders) -> None:
    with pytest.raises(KeyError):
        mutable_headers["bar"]


def test_mutable_scope_headers_setitem_existing_key(
    raw_headers: "RawHeadersList", mutable_headers: MutableScopeHeaders, existing_headers_key: str
) -> None:
    mutable_headers[existing_headers_key] = "baz"
    assert raw_headers == [(b"foo", b"baz")]


def test_mutable_scope_headers_from_tuple_setitem_existing_key(
    raw_headers_tuple: "RawHeaders", mutable_headers_from_tuple: MutableScopeHeaders, existing_headers_key: str
) -> None:
    mutable_headers_from_tuple[existing_headers_key] = "baz"
    assert list(raw_headers_tuple) == [(b"foo", b"baz")]


def test_mutable_scope_headers_setitem_new_key(
    raw_headers: "RawHeadersList", mutable_headers: MutableScopeHeaders
) -> None:
    mutable_headers["bar"] = "baz"
    assert raw_headers == [(b"foo", b"bar"), (b"bar", b"baz")]


def test_mutable_scope_headers_setitem_delitem(
    raw_headers: "RawHeadersList", mutable_headers: MutableScopeHeaders, existing_headers_key: str
) -> None:
    mutable_headers.add("foo", "baz")
    mutable_headers["bar"] = "baz"
    del mutable_headers[existing_headers_key]
    assert raw_headers == [(b"bar", b"baz")]


def test_mutable_scope_headers_setdefault() -> None:
    headers = MutableScopeHeaders()

    assert headers.setdefault("foo", "bar") == "bar"
    assert headers.setdefault("foo", "baz") == "bar"
    assert headers.getall("foo") == ["bar"]


def test_mutable_scope_header_len(mutable_headers: MutableScopeHeaders) -> None:
    assert len(mutable_headers) == 1
    mutable_headers.add("foo", "bar")
    assert len(mutable_headers) == 2
    mutable_headers["bar"] = "baz"
    assert len(mutable_headers) == 3


def test_mutable_scope_header_iter(mutable_headers: MutableScopeHeaders) -> None:
    mutable_headers.add("foo", "baz")
    mutable_headers["bar"] = "zab"
    assert list(mutable_headers) == ["foo", "foo", "bar"]


def test_cache_control_to_header() -> None:
    header = CacheControlHeader(max_age=10, private=True)
    expected_header_values = ["max-age=10, private", "private, max-age=10"]
    assert header.to_header() in expected_header_values
    assert header.to_header(include_header_name=True) in [f"cache-control: {v}" for v in expected_header_values]


def test_cache_control_from_header() -> None:
    header_value = (
        "public, private, no-store, no-cache, max-age=10000, s-maxage=1000, no-transform, "
        "must-revalidate, proxy-revalidate, must-understand, immutable, stale-while-revalidate=100"
    )
    header = CacheControlHeader.from_header(header_value)
    assert simple_asdict(header) == {
        "documentation_only": False,
        "public": True,
        "private": True,
        "no_store": True,
        "no_cache": True,
        "max_age": 10000,
        "s_maxage": 1000,
        "no_transform": True,
        "must_revalidate": True,
        "proxy_revalidate": True,
        "must_understand": True,
        "immutable": True,
        "stale_while_revalidate": 100,
    }


def test_cache_control_from_header_single_value() -> None:
    header_value = "no-cache"
    header = CacheControlHeader.from_header(header_value)
    header_dict = simple_asdict(header, exclude_none=True)
    assert header_dict == {"no_cache": True, "documentation_only": False}


@pytest.mark.parametrize("invalid_value", ["x=y=z", "x, ", "no-cache=10", "invalid-header=10"])
def test_cache_control_from_header_invalid_value(invalid_value: str) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        CacheControlHeader.from_header(invalid_value)


def test_cache_control_header_prevent_storing() -> None:
    header = CacheControlHeader.prevent_storing()
    header_dict = simple_asdict(header, exclude_none=True)
    assert header_dict == {"no_store": True, "documentation_only": False}


def test_cache_control_header_unsupported_type_annotation() -> None:
    @dataclass
    class InvalidCacheControlHeader(CacheControlHeader):
        unsupported_type: Union[int, str] = "foo"

    with pytest.raises(ImproperlyConfiguredException):
        InvalidCacheControlHeader.from_header("unsupported_type")


def test_etag_documentation_only() -> None:
    assert ETag(documentation_only=True).value is None


def test_etag_no_value() -> None:
    with pytest.raises(ValidationException):
        ETag()

    with pytest.raises(ValidationException):
        ETag(weak=True)


def test_etag_non_ascii() -> None:
    with pytest.raises(ValueError):
        ETag(value="f↓o")


def test_etag_from_header() -> None:
    etag = ETag.from_header('"foo"')
    assert etag.value == "foo"
    assert etag.weak is False


@pytest.mark.parametrize("value", ['W/"foo"', 'w/"foo"'])
def test_etag_from_header_weak(value: str) -> None:
    etag = ETag.from_header(value)
    assert etag.value == "foo"
    assert etag.weak is True


@pytest.mark.parametrize("value", ['"føo"', 'W/"føo"'])
def test_etag_from_header_non_ascii_value(value: str) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        ETag.from_header(value)


@pytest.mark.parametrize("value", ["foo", "W/foo"])
def test_etag_from_header_missing_quotes(value: str) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        ETag.from_header(value)


def test_etag_to_header() -> None:
    assert ETag(value="foo").to_header() == '"foo"'


def test_etag_to_header_weak() -> None:
    assert ETag(value="foo", weak=True).to_header() == 'W/"foo"'


@pytest.mark.parametrize(
    "accept_value,provided_types,best_match",
    (
        ("text/plain", ["text/plain"], "text/plain"),
        ("text/plain", [MediaType.TEXT], MediaType.TEXT),
        ("text/plain", ["text/plain"], "text/plain"),
        ("text/plain", ["text/html"], None),
        ("text/*", ["text/html"], "text/html"),
        ("*/*", ["text/html"], "text/html"),
        ("text/plain;p=test", ["text/plain"], "text/plain"),
        ("text/plain", ["text/plain;p=test"], None),
        ("text/plain;p=test", ["text/plain;p=test"], "text/plain;p=test"),
        ("text/plain", ["text/*"], "text/plain"),
        ("text/html", ["*/*"], "text/html"),
        ("text/plain;q=0.8,text/html", ["text/plain", "text/html"], "text/html"),
        ("text/*,text/html", ["text/plain", "text/html"], "text/html"),
    ),
)
def test_accept_best_match(accept_value: str, provided_types: List[str], best_match: Optional[str]) -> None:
    accept = Accept(accept_value)
    assert accept.best_match(provided_types) == best_match


def test_accept_accepts() -> None:
    accept = Accept("text/plain;q=0.8,text/html")
    assert accept.accepts(MediaType.TEXT)
