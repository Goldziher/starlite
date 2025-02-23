from __future__ import annotations

import asyncio
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock

import pytest
import trio
from pytest_mock import MockerFixture

from litestar.concurrency import (
    _State,
    get_asyncio_executor,
    get_trio_capacity_limiter,
    set_asyncio_executor,
    set_trio_capacity_limiter,
    sync_to_thread,
)


@pytest.fixture(autouse=True)
def reset_state() -> Generator[None, None, None]:
    _State.LIMITER = None
    _State.EXECUTOR = None
    yield
    _State.LIMITER = None
    _State.EXECUTOR = None


def func() -> int:
    return 1


def test_sync_to_thread_asyncio() -> None:
    loop = asyncio.new_event_loop()
    assert loop.run_until_complete(sync_to_thread(func)) == 1


def test_sync_to_thread_trio() -> None:
    assert trio.run(sync_to_thread, func) == 1


def test_get_set_asyncio_executor() -> None:
    assert get_asyncio_executor() is None
    executor = ThreadPoolExecutor()
    set_asyncio_executor(executor)
    assert get_asyncio_executor() is executor


def test_get_set_trio_capacity_limiter() -> None:
    limiter = trio.CapacityLimiter(10)
    assert get_trio_capacity_limiter() is None
    set_trio_capacity_limiter(limiter)
    assert get_trio_capacity_limiter() is limiter


def test_asyncio_uses_executor(mocker: MockerFixture) -> None:
    executor = ThreadPoolExecutor()

    mocker.patch("litestar.concurrency.get_asyncio_executor", return_value=executor)
    mock_run_in_executor = AsyncMock()
    mocker.patch("litestar.concurrency.asyncio.get_running_loop").return_value.run_in_executor = mock_run_in_executor

    loop = asyncio.new_event_loop()
    loop.run_until_complete(sync_to_thread(func))

    assert mock_run_in_executor.call_args_list[0].args[0] is executor


def test_set_asyncio_executor_from_running_loop_raises() -> None:
    async def main() -> None:
        set_asyncio_executor(ThreadPoolExecutor())

    with pytest.raises(RuntimeError):
        asyncio.new_event_loop().run_until_complete(main())

    assert get_asyncio_executor() is None


def test_trio_uses_limiter(mocker: MockerFixture) -> None:
    limiter = trio.CapacityLimiter(10)
    mocker.patch("litestar.concurrency.get_trio_capacity_limiter", return_value=limiter)
    mock_run_sync = mocker.patch("trio.to_thread.run_sync", new_callable=AsyncMock)

    trio.run(sync_to_thread, func)

    assert mock_run_sync.call_args_list[0].kwargs["limiter"] is limiter


def test_set_trio_capacity_limiter_from_async_context_raises() -> None:
    async def main() -> None:
        set_trio_capacity_limiter(trio.CapacityLimiter(1))

    with pytest.raises(RuntimeError):
        trio.run(main)

    assert get_trio_capacity_limiter() is None


def test_sync_to_thread_unsupported_lib(mocker: MockerFixture) -> None:
    mocker.patch("litestar.concurrency.sniffio.current_async_library", return_value="something")

    with pytest.raises(RuntimeError):
        asyncio.new_event_loop().run_until_complete(sync_to_thread(func))
