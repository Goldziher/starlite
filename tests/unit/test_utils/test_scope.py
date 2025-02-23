from __future__ import annotations

from litestar.utils.scope.state import CONNECTION_STATE_KEY, ScopeState


def test_from_scope_without_state() -> None:
    scope = {}  # type: ignore[var-annotated]
    state = ScopeState.from_scope(scope)  # type: ignore[arg-type]
    assert scope["state"][CONNECTION_STATE_KEY] is state
