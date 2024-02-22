from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pytest

from litestar.types.empty import Empty
from litestar.utils import (
    delete_litestar_scope_state,
    get_litestar_scope_state,
    set_litestar_scope_state,
)
from litestar.utils.scope.state import CONNECTION_STATE_KEY, ScopeState

if TYPE_CHECKING:
    from litestar.types.asgi_types import Scope


@pytest.fixture()
def scope(create_scope: Callable[..., Scope]) -> Scope:
    return create_scope()


def test_from_scope_without_state() -> None:
    scope = {}  # type: ignore[var-annotated]
    state = ScopeState.from_scope(scope)  # type: ignore[arg-type]
    assert scope["state"][CONNECTION_STATE_KEY] is state


@pytest.mark.parametrize(("pop",), [(True,), (False,)])
def test_get_litestar_scope_state_arbitrary_value(pop: bool, scope: Scope) -> None:
    key = "test"
    value = {"key": "value"}
    connection_state = ScopeState.from_scope(scope)
    connection_state._compat_ns[key] = value
    retrieved_value = get_litestar_scope_state(scope, key, pop=pop)
    assert retrieved_value == value
    if pop:
        assert connection_state._compat_ns.get(key) is None
    else:
        assert connection_state._compat_ns.get(key) == value


@pytest.mark.parametrize(("pop",), [(True,), (False,)])
def test_get_litestar_scope_state_defined_value(pop: bool, scope: Scope) -> None:
    connection_state = ScopeState.from_scope(scope)
    connection_state.is_cached = True
    assert get_litestar_scope_state(scope, "is_cached", pop=pop) is True
    if pop:
        assert connection_state.is_cached is Empty  # type: ignore[comparison-overlap]
    else:
        assert connection_state.is_cached is True


def test_set_litestar_scope_state_arbitrary_value(scope: Scope) -> None:
    connection_state = ScopeState.from_scope(scope)
    set_litestar_scope_state(scope, "key", "value")
    assert connection_state._compat_ns["key"] == "value"


def test_set_litestar_scope_state_defined_value(scope: Scope) -> None:
    connection_state = ScopeState.from_scope(scope)
    set_litestar_scope_state(scope, "is_cached", True)
    assert connection_state.is_cached is True


def test_delete_litestar_scope_state_arbitrary_value(scope: Scope) -> None:
    connection_state = ScopeState.from_scope(scope)
    connection_state._compat_ns["key"] = "value"
    delete_litestar_scope_state(scope, "key")
    assert "key" not in connection_state._compat_ns


def test_delete_litestar_scope_state_defined_value(scope: Scope) -> None:
    connection_state = ScopeState.from_scope(scope)
    connection_state.is_cached = True
    delete_litestar_scope_state(scope, "is_cached")
    assert connection_state.is_cached is Empty  # type: ignore[comparison-overlap]
