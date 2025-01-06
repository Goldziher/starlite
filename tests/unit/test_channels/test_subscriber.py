from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from litestar.channels import Subscriber
from litestar.channels.subscriber import BacklogStrategy
from litestar.utils.compat import async_next

from .util import get_from_stream

pytestmark = pytest.mark.anyio


async def test_subscriber_backlog_backoff() -> None:
    subscriber = Subscriber(plugin=MagicMock(), max_backlog=2, backlog_strategy="backoff")

    assert subscriber.put_nowait(b"foo")
    assert subscriber.put_nowait(b"bar")
    assert not subscriber.put_nowait(b"baz")

    assert subscriber.qsize == 2
    assert [subscriber._queue.get_nowait(), subscriber._queue.get_nowait()] == [b"foo", b"bar"]
    await subscriber.stop()


async def test_subscriber_backlog_dropleft() -> None:
    subscriber = Subscriber(plugin=MagicMock(), max_backlog=2, backlog_strategy="dropleft")

    assert subscriber.put_nowait(b"foo")
    assert subscriber.put_nowait(b"bar")
    assert subscriber.put_nowait(b"baz")

    assert subscriber.qsize == 2
    assert [subscriber._queue.get_nowait(), subscriber._queue.get_nowait()] == [b"bar", b"baz"]
    await subscriber.stop()


async def test_iter_events_none_breaks() -> None:
    subscriber = Subscriber(MagicMock())
    mock_callback = MagicMock()

    subscriber.put_nowait(b"foo")
    subscriber.put_nowait(None)

    async def consume() -> None:
        async for event in subscriber.iter_events():
            mock_callback(event)

    await asyncio.wait_for(consume(), timeout=0.1)

    mock_callback.assert_called_once_with(b"foo")


@pytest.mark.parametrize("join", [False, True])
async def test_stop(join: bool) -> None:
    subscriber = Subscriber(AsyncMock())
    async with subscriber.run_in_background(AsyncMock()):
        assert subscriber._task
        assert subscriber.is_running

        subscriber.put_nowait(b"foo")

        await subscriber.stop(join=join)

        assert subscriber._task is None


async def test_stop_with_task_done() -> None:
    subscriber = Subscriber(AsyncMock())
    async with subscriber.run_in_background(AsyncMock()):
        assert subscriber._task
        assert subscriber.is_running

        subscriber.put_nowait(None)

        await subscriber.stop(join=True)

        assert subscriber._task is None


@pytest.mark.parametrize("join", [False, True])
async def test_stop_no_task(join: bool) -> None:
    subscriber = Subscriber(AsyncMock())

    await subscriber.stop(join=join)


async def test_qsize() -> None:
    subscriber = Subscriber(AsyncMock())

    assert not subscriber.qsize
    subscriber.put_nowait(b"foo")

    assert subscriber.qsize == 1

    await async_next(subscriber.iter_events())

    assert not subscriber.qsize


@pytest.mark.parametrize("backlog_strategy", ["backoff", "dropleft"])
async def test_backlog(backlog_strategy: BacklogStrategy) -> None:
    messages = [b"foo", b"bar", b"baz"]
    subscriber = Subscriber(AsyncMock(), backlog_strategy=backlog_strategy, max_backlog=2)
    expected_messages = messages[:-1] if backlog_strategy == "backoff" else messages[1:]
    for message in messages:
        subscriber.put_nowait(message)

    assert subscriber.qsize == 2
    enqueued_items = await get_from_stream(subscriber, 2)

    assert expected_messages == enqueued_items


async def tests_run_in_background_run_in_background_called_while_running_raises() -> None:
    subscriber = Subscriber(AsyncMock())

    async with subscriber.run_in_background(AsyncMock()):
        with pytest.raises(RuntimeError):
            async with subscriber.run_in_background(AsyncMock()):
                pass
