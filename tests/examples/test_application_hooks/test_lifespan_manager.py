from unittest.mock import AsyncMock

import pytest
from docs.examples.application_hooks.lifespan_manager import app
from pytest_mock import MockerFixture

from litestar import get
from litestar.datastructures import State
from litestar.testing import TestClient


class FakeAsyncEngine:
    dispose = AsyncMock()


@pytest.mark.anyio
async def test_startup_and_shutdown_example(mocker: MockerFixture) -> None:
    mock_create_engine = mocker.patch("docs.examples.application_hooks.lifespan_manager.create_async_engine")
    mock_create_engine.return_value = FakeAsyncEngine

    @get("/")
    def handler(state: State) -> None:
        assert state.engine is mock_create_engine.return_value

    app.register(handler)

    with TestClient(app=app) as client:
        client.get("/")

    FakeAsyncEngine.dispose.assert_awaited_once()
