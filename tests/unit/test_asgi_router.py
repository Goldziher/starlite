from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, Callable
from unittest.mock import AsyncMock, MagicMock, call

import anyio
import pytest
from pytest_mock import MockerFixture

from litestar import Litestar, asgi
from litestar._asgi.asgi_router import ASGIRouter
from litestar.exceptions import ImproperlyConfiguredException
from litestar.testing import TestClient, create_test_client
from litestar.utils.helpers import get_exception_group

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

    from litestar.types import Receive, Scope, Send

_ExceptionGroup = get_exception_group()


def test_add_mount_route_disallow_path_parameter() -> None:
    async def handler(scope: Scope, receive: Receive, send: Send) -> None:
        return None

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[asgi("/mount-path", is_static=True)(handler), asgi("/mount-path/{id:str}")(handler)])


class _LifeSpanCallable:
    def __init__(self, should_raise: bool = False) -> None:
        self.called = False
        self.should_raise = should_raise

    def __call__(self) -> None:
        self.called = True
        if self.should_raise:
            raise RuntimeError("damn")


def test_life_span_startup() -> None:
    life_span_callable = _LifeSpanCallable()
    with create_test_client([], on_startup=[life_span_callable]):
        assert life_span_callable.called


def test_life_span_startup_error_handling() -> None:
    life_span_callable = _LifeSpanCallable(should_raise=True)

    with pytest.raises(_ExceptionGroup), create_test_client([], on_startup=[life_span_callable]):
        pass


def test_life_span_shutdown() -> None:
    life_span_callable = _LifeSpanCallable()
    with create_test_client([], on_shutdown=[life_span_callable]):
        pass
    assert life_span_callable.called


def test_life_span_shutdown_error_handling() -> None:
    life_span_callable = _LifeSpanCallable(should_raise=True)
    with pytest.raises(RuntimeError), create_test_client([], on_shutdown=[life_span_callable]):
        pass


@pytest.fixture
def startup_mock() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def shutdown_mock() -> AsyncMock:
    return AsyncMock()


LifeSpanManager = Callable[[Litestar], "AbstractAsyncContextManager[None]"]


def create_lifespan_manager(startup_mock: AsyncMock, shutdown_mock: AsyncMock) -> LifeSpanManager:
    @asynccontextmanager
    async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
        try:
            await startup_mock(app)
            yield
        finally:
            await shutdown_mock()

    return lifespan


@pytest.fixture()
def lifespan_manager(startup_mock: AsyncMock, shutdown_mock: AsyncMock) -> LifeSpanManager:
    return create_lifespan_manager(startup_mock, shutdown_mock)


def test_lifespan_context_manager(
    lifespan_manager: LifeSpanManager, startup_mock: AsyncMock, shutdown_mock: AsyncMock
) -> None:
    with create_test_client(lifespan=[lifespan_manager]):
        assert startup_mock.call_count == 1
        assert shutdown_mock.call_count == 0

    assert shutdown_mock.call_count == 1


def test_lifespan_context_manager_with_hooks(
    lifespan_manager: LifeSpanManager, startup_mock: AsyncMock, shutdown_mock: AsyncMock
) -> None:
    on_startup_hook_mock = AsyncMock()
    on_shutdown_hook_mock = AsyncMock()

    async def on_startup() -> None:
        await on_startup_hook_mock()

    async def on_shutdown() -> None:
        await on_shutdown_hook_mock()

    with create_test_client(lifespan=[lifespan_manager], on_startup=[on_startup], on_shutdown=[on_shutdown]):
        assert startup_mock.call_count == 1
        assert on_startup_hook_mock.call_count == 1
        assert shutdown_mock.call_count == 0
        assert on_shutdown_hook_mock.call_count == 0

    assert shutdown_mock.call_count == 1
    assert on_shutdown_hook_mock.call_count == 1


def test_multiple_lifespan_managers() -> None:
    managers: list[Callable[[Litestar], AbstractAsyncContextManager] | AbstractAsyncContextManager] = []
    startup_mocks: list[AsyncMock] = []
    shutdown_mocks: list[AsyncMock] = []
    for _ in range(3):
        startup_mock = AsyncMock()
        shutdown_mock = AsyncMock()
        managers.append(create_lifespan_manager(startup_mock, shutdown_mock))
        startup_mocks.append(startup_mock)
        shutdown_mocks.append(shutdown_mock)

    app = Litestar(lifespan=managers)
    with TestClient(app=app):
        for m in startup_mocks:
            m.assert_called_once_with(app)
        assert all(m.call_count == 0 for m in shutdown_mocks)

    assert all(m.call_count == 1 for m in startup_mocks)
    assert all(m.call_count == 1 for m in shutdown_mocks)


@pytest.fixture()
def mock_format_exc(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("litestar._asgi.asgi_router.format_exc")


async def test_lifespan_startup_failure(mock_format_exc: MagicMock) -> None:
    receive = AsyncMock()
    receive.return_value = {"type": "lifespan.startup"}
    send = AsyncMock()
    exception = ValueError("foo")
    mock_format_exc.return_value = str(exception)

    mock_on_startup = AsyncMock(side_effect=exception)

    async def on_startup() -> None:
        await mock_on_startup()

    router = ASGIRouter(app=Litestar(on_startup=[on_startup]))

    with pytest.raises(_ExceptionGroup):
        await router.lifespan(receive, send)

    assert send.call_count == 1
    send.assert_called_once_with({"type": "lifespan.startup.failed", "message": mock_format_exc.return_value})


async def test_lifespan_shutdown_failure(mock_format_exc: MagicMock) -> None:
    receive = AsyncMock()
    receive.return_value = {"type": "lifespan.shutdown"}
    send = AsyncMock()
    exception = ValueError("foo")
    mock_format_exc.return_value = str(exception)

    mock_on_shutdown = AsyncMock(side_effect=exception)

    async def on_shutdown() -> None:
        await mock_on_shutdown()

    router = ASGIRouter(app=Litestar(on_shutdown=[on_shutdown]))

    with pytest.raises(ValueError):
        await router.lifespan(receive, send)

    assert send.call_count == 2
    assert send.call_args_list[1][0][0] == {"type": "lifespan.shutdown.failed", "message": mock_format_exc.return_value}


async def test_lifespan_context_exception_after_startup(mock_format_exc: MagicMock) -> None:
    receive = AsyncMock()
    receive.return_value = {"type": "lifespan.startup"}
    send = AsyncMock()
    mock_format_exc.return_value = "foo"

    async def sleep_and_raise() -> None:
        await anyio.sleep(0)
        raise RuntimeError("An error occurred")

    @asynccontextmanager
    async def lifespan(_: Litestar) -> AsyncGenerator[None, None]:
        async with anyio.create_task_group() as tg:
            tg.start_soon(sleep_and_raise)
            yield

    router = ASGIRouter(app=Litestar(lifespan=[lifespan]))

    with pytest.raises(_ExceptionGroup):
        await router.lifespan(receive, send)

    assert receive.call_count == 2
    send.assert_has_calls(
        [
            call({"type": "lifespan.startup.complete"}),
            call({"type": "lifespan.shutdown.failed", "message": mock_format_exc.return_value}),
        ]
    )
