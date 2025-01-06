from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from docs.examples import startup_and_shutdown

from litestar import get
from litestar.datastructures import State
from litestar.testing import TestClient

if TYPE_CHECKING:
    from pytest import MonkeyPatch


class FakeAsyncEngine:
    dispose = AsyncMock()


@pytest.mark.anyio
async def test_startup_and_shutdown_example(monkeypatch: "MonkeyPatch") -> None:
    monkeypatch.setattr(startup_and_shutdown, "create_async_engine", MagicMock(return_value=FakeAsyncEngine))

    @get("/")
    def handler(state: State) -> None:
        assert state.engine is FakeAsyncEngine

    startup_and_shutdown.app.register(handler)

    with TestClient(app=startup_and_shutdown.app) as client:
        client.get("/")
    FakeAsyncEngine.dispose.assert_awaited_once()
