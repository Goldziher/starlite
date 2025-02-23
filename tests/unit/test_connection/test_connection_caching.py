from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, Callable
from unittest.mock import ANY, MagicMock, call

import pytest

from litestar import Request, post
from litestar.testing import RequestFactory
from litestar.types import Empty, HTTPReceiveMessage, Scope
from litestar.utils.scope.state import ScopeState


async def test_multiple_request_object_data_caching(create_scope: Callable[..., Scope], mock: MagicMock) -> None:
    """Test that accessing the request data on multiple request objects only attempts to await `receive()` once.

    https://github.com/litestar-org/litestar/issues/2727
    """

    @post("/", request_max_body_size=None)
    async def handler() -> None:
        pass

    async def test_receive() -> HTTPReceiveMessage:
        mock()
        return {"type": "http.request", "body": b"abc", "more_body": False}

    scope = create_scope(route_handler=handler)
    request_1 = Request[Any, Any, Any](scope, test_receive)
    request_2 = Request[Any, Any, Any](scope, test_receive)
    assert (await request_1.body()) == b"abc"
    assert (await request_2.body()) == b"abc"
    assert mock.call_count == 1


@pytest.fixture(name="get_mock")
def get_mock_fixture() -> MagicMock:
    return MagicMock()


@pytest.fixture(name="set_mock")
def set_mock_fixture() -> MagicMock:
    return MagicMock()


@pytest.fixture(name="create_connection")
def create_connection_fixture(
    get_mock: MagicMock, set_mock: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> Callable[..., Request]:
    class MockScopeState(ScopeState):
        def __getattribute__(self, key: str) -> Any:
            get_mock(key)
            return object.__getattribute__(self, key)

        def __setattr__(self, key: str, value: Any) -> None:
            set_mock(key, value)
            super().__setattr__(key, value)

    def create_connection(body_type: str = "json") -> Request:
        monkeypatch.setattr("litestar.connection.base.ScopeState", MockScopeState)
        connection = RequestFactory().get()

        async def fake_receive() -> HTTPReceiveMessage:
            if body_type == "msgpack":
                return {"type": "http.request", "body": b"\x81\xa3abc\xa3def", "more_body": False}
            return {"type": "http.request", "body": b'{"abc":"def"}', "more_body": False}

        monkeypatch.setattr(connection, "receive", fake_receive)

        return connection

    return create_connection


@pytest.fixture(name="get_value")
def get_value_fixture() -> Callable[[Request, str, bool], Awaitable[Any]]:
    """Fixture to get the value of a connection cached property.

    Returns:
        A function to get the value of a connection cached property.
    """

    async def get_value_(connection: Request, prop_name: str, is_coro: bool) -> Any:
        """Helper to get the value of the tested cached property."""
        value = getattr(connection, prop_name)
        return await value() if is_coro else value

    return get_value_


caching_tests = [
    ("url", "url", "_url", False),
    ("base_url", "base_url", "_base_url", False),
    ("parsed_query", "query_params", "_parsed_query", False),
    ("cookies", "cookies", "_cookies", False),
    ("body", "body", "_body", True),
    ("form", "form", "_form", True),
    ("msgpack", "msgpack", "_msgpack", True),
    ("json", "json", "_json", True),
    ("accept", "accept", "_accept", False),
    ("content_type", "content_type", "_content_type", False),
]


@pytest.mark.parametrize(("state_key", "prop_name", "cache_attr_name", "is_coro"), caching_tests)
async def test_connection_cached_properties_no_scope_or_connection_caching(
    state_key: str,
    prop_name: str,
    cache_attr_name: str,
    is_coro: bool,
    create_connection: Callable[..., Request],
    get_mock: MagicMock,
    set_mock: MagicMock,
    get_value: Callable[[Request, str, bool], Awaitable[Any]],
) -> None:
    def check_get_mock() -> None:
        """Helper to check the get mock.

        For certain properties, we call `get_litestar_scope_state()` twice, once for the property and once for the
        body. For these cases, we check that the mock was called twice.
        """
        if state_key in {"json", "msgpack"}:
            get_mock.assert_has_calls([call(state_key), call("body")])
        elif state_key in {"accept", "cookies", "content_type"}:
            get_mock.assert_has_calls([call(state_key), call("headers")])
        elif state_key == "form":
            get_mock.assert_has_calls([call(state_key), call("content_type")])
        elif state_key == "body":
            get_mock.assert_has_calls([call(state_key), call("headers")])
        else:
            get_mock.assert_called_once_with(state_key)

    def check_set_mock() -> None:
        """Helper to check the set mock.

        For certain properties, we call `set_litestar_scope_state()` twice, once for the property and once for the
        body. For these cases, we check that the mock was called twice.
        """
        if state_key in {"json", "msgpack"}:
            set_mock.assert_has_calls([call("body", ANY), call(state_key, ANY)])
        elif state_key == "form":
            set_mock.assert_has_calls([call("content_type", ANY), call(state_key, ANY)])
        elif state_key in {"accept", "cookies", "content_type"}:
            set_mock.assert_has_calls([call("headers", ANY), call(state_key, ANY)])
        elif state_key == "body":
            set_mock.assert_has_calls([call("headers", ANY), call(state_key, ANY)])
        else:
            set_mock.assert_called_once_with(state_key, ANY)

    connection = create_connection("msgpack" if state_key == "msgpack" else "json")
    connection_state = connection._connection_state

    assert getattr(connection_state, state_key) is Empty
    setattr(connection, cache_attr_name, Empty)

    get_mock.reset_mock()
    set_mock.reset_mock()
    await get_value(connection, prop_name, is_coro)
    check_get_mock()
    check_set_mock()


@pytest.mark.parametrize(("state_key", "prop_name", "cache_attr_name", "is_coro"), caching_tests)
async def test_connection_cached_properties_cached_in_scope(
    state_key: str,
    prop_name: str,
    cache_attr_name: str,
    is_coro: bool,
    create_connection: Callable[..., Request],
    get_mock: MagicMock,
    set_mock: MagicMock,
    get_value: Callable[[Request, str, bool], Awaitable[Any]],
) -> None:
    # set the value in the scope and ensure empty on connection
    connection = create_connection()
    connection_state = ScopeState.from_scope(connection.scope)

    setattr(connection_state, state_key, {"not": "empty"})
    setattr(connection, cache_attr_name, Empty)

    get_mock.reset_mock()
    set_mock.reset_mock()
    await get_value(connection, prop_name, is_coro)
    get_mock.assert_called_once_with(state_key)
    set_mock.assert_not_called()


@pytest.mark.parametrize(("state_key", "prop_name", "cache_attr_name", "is_coro"), caching_tests)
async def test_connection_cached_properties_cached_on_connection(
    state_key: str,
    prop_name: str,
    cache_attr_name: str,
    is_coro: bool,
    create_connection: Callable[..., Request],
    get_mock: MagicMock,
    set_mock: MagicMock,
    get_value: Callable[[Request, str, bool], Awaitable[Any]],
) -> None:
    connection = create_connection()
    # set the value on the connection
    setattr(connection, cache_attr_name, {"not": "empty"})
    get_mock.reset_mock()
    set_mock.reset_mock()
    await get_value(connection, prop_name, is_coro)
    get_mock.assert_not_called()
    set_mock.assert_not_called()
