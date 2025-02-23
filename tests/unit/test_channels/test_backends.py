from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from _pytest.fixtures import FixtureRequest
from redis.asyncio.client import Redis

from litestar.channels import ChannelsBackend
from litestar.channels.backends.asyncpg import AsyncPgChannelsBackend
from litestar.channels.backends.memory import MemoryChannelsBackend
from litestar.channels.backends.psycopg import PsycoPgChannelsBackend
from litestar.channels.backends.redis import RedisChannelsStreamBackend
from litestar.exceptions import ImproperlyConfiguredException
from litestar.utils.compat import async_next


@pytest.fixture(
    params=[
        pytest.param("redis_pub_sub_backend", id="redis:pubsub", marks=pytest.mark.xdist_group("redis")),
        pytest.param("redis_stream_backend", id="redis:stream", marks=pytest.mark.xdist_group("redis")),
        pytest.param("postgres_asyncpg_backend", id="postgres:asyncpg", marks=pytest.mark.xdist_group("postgres")),
        pytest.param("postgres_psycopg_backend", id="postgres:psycopg", marks=pytest.mark.xdist_group("postgres")),
        pytest.param("memory_backend", id="memory"),
    ]
)
def channels_backend_instance(request: FixtureRequest) -> ChannelsBackend:
    return cast(ChannelsBackend, request.getfixturevalue(request.param))


@pytest.fixture(
    params=[
        pytest.param(
            "redis_stream_backend_with_history", id="redis:stream+history", marks=pytest.mark.xdist_group("redis")
        ),
        pytest.param("memory_backend_with_history", id="memory+history"),
    ]
)
def channels_backend_instance_with_history(request: FixtureRequest) -> ChannelsBackend:
    return cast(ChannelsBackend, request.getfixturevalue(request.param))


@pytest.fixture()
async def channels_backend(channels_backend_instance: ChannelsBackend) -> AsyncGenerator[ChannelsBackend, None]:
    await channels_backend_instance.on_startup()
    yield channels_backend_instance
    await channels_backend_instance.on_shutdown()


@pytest.fixture()
async def channels_backend_with_history(
    channels_backend_instance_with_history: ChannelsBackend,
) -> AsyncGenerator[ChannelsBackend, None]:
    await channels_backend_instance_with_history.on_startup()
    yield channels_backend_instance_with_history
    await channels_backend_instance_with_history.on_shutdown()


@pytest.mark.parametrize("channels", [{"foo"}, {"foo", "bar"}])
async def test_pub_sub(channels_backend: ChannelsBackend, channels: set[str]) -> None:
    await channels_backend.subscribe(channels)
    await channels_backend.publish(b"something", channels)

    event_generator = channels_backend.stream_events()
    received = set()
    for _ in channels:
        received.add(await async_next(event_generator))
    assert received == {(c, b"something") for c in channels}


async def test_pub_sub_unsubscribe(channels_backend: ChannelsBackend) -> None:
    await channels_backend.subscribe(["foo", "bar"])
    await channels_backend.publish(b"something", ["foo"])

    event_generator = channels_backend.stream_events()
    await channels_backend.unsubscribe(["foo"])
    await channels_backend.publish(b"something", ["bar"])

    assert await asyncio.wait_for(async_next(event_generator), timeout=0.01) == ("bar", b"something")


async def test_pub_sub_no_subscriptions(channels_backend: ChannelsBackend) -> None:
    await channels_backend.publish(b"something", ["foo"])

    event_generator = channels_backend.stream_events()
    with pytest.raises((asyncio.TimeoutError, TimeoutError)):
        await asyncio.wait_for(async_next(event_generator), timeout=0.01)


@pytest.mark.flaky(reruns=5)  # this should not really happen but just in case, we retry
async def test_pub_sub_no_subscriptions_by_unsubscribes(channels_backend: ChannelsBackend) -> None:
    await channels_backend.subscribe(["foo", "bar"])
    await channels_backend.publish(b"something", ["foo"])

    event_generator = channels_backend.stream_events()
    await asyncio.wait_for(async_next(event_generator), timeout=0.01)
    await channels_backend.unsubscribe(["foo"])
    await channels_backend.publish(b"something", ["foo"])

    with pytest.raises((asyncio.TimeoutError, TimeoutError)):
        await asyncio.wait_for(async_next(event_generator), timeout=0.01)


async def test_pub_sub_shutdown_leftover_messages(channels_backend_instance: ChannelsBackend) -> None:
    await channels_backend_instance.on_startup()

    await channels_backend_instance.publish(b"something", {"foo"})

    await asyncio.wait_for(channels_backend_instance.on_shutdown(), timeout=0.1)


async def test_unsubscribe_without_subscription(channels_backend: ChannelsBackend) -> None:
    await channels_backend.unsubscribe(["foo"])


@pytest.mark.parametrize("history_limit,expected_history_length", [(None, 10), (1, 1), (5, 5), (10, 10)])
async def test_get_history(
    channels_backend_with_history: ChannelsBackend, history_limit: int | None, expected_history_length: int
) -> None:
    messages = [str(i).encode() for i in range(100)]
    for message in messages:
        await channels_backend_with_history.publish(message, {"something"})

    history = await channels_backend_with_history.get_history("something", history_limit)

    expected_messages = messages[-expected_history_length:]
    assert len(history) == expected_history_length
    assert history == expected_messages


async def test_discards_history_entries(channels_backend_with_history: ChannelsBackend) -> None:
    for _ in range(20):
        await channels_backend_with_history.publish(b"foo", {"bar"})

    assert len(await channels_backend_with_history.get_history("bar")) == 10


@pytest.mark.xdist_group("redis")
async def test_redis_streams_backend_flushall(redis_stream_backend: RedisChannelsStreamBackend) -> None:
    await redis_stream_backend.publish(b"something", ["foo", "bar", "baz"])

    result = await redis_stream_backend.flush_all()

    assert result == 3


@pytest.mark.flaky(reruns=5)  # this should not really happen but just in case, we retry
@pytest.mark.xdist_group("redis")
async def test_redis_stream_backend_expires(redis_client: Redis) -> None:
    backend = RedisChannelsStreamBackend(redis=redis_client, stream_ttl=timedelta(milliseconds=10), history=2)

    await backend.publish(b"something", ["foo"])
    await asyncio.sleep(0.1)
    await backend.publish(b"something", ["bar"])

    assert not await backend._redis.xrange(backend._make_key("foo"))
    assert await backend._redis.xrange(backend._make_key("bar"))


async def test_memory_publish_not_initialized_raises() -> None:
    backend = MemoryChannelsBackend()

    with pytest.raises(RuntimeError):
        await backend.publish(b"foo", ["something"])


@pytest.mark.xdist_group("postgres")
async def test_asyncpg_get_history(postgres_asyncpg_backend: AsyncPgChannelsBackend) -> None:
    with pytest.raises(NotImplementedError):
        await postgres_asyncpg_backend.get_history("something")


@pytest.mark.xdist_group("postgres")
async def test_psycopg_get_history(postgres_psycopg_backend: PsycoPgChannelsBackend) -> None:
    with pytest.raises(NotImplementedError):
        await postgres_psycopg_backend.get_history("something")


async def test_asyncpg_make_connection() -> None:
    make_connection = AsyncMock()

    backend = AsyncPgChannelsBackend(make_connection=make_connection)
    await backend.on_startup()

    make_connection.assert_awaited_once()


async def test_asyncpg_no_make_conn_or_dsn_passed_raises() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        AsyncPgChannelsBackend()  # type: ignore[call-overload]


def test_asyncpg_listener_raises_on_non_string_payload() -> None:
    backend = AsyncPgChannelsBackend(make_connection=AsyncMock())
    with pytest.raises(RuntimeError):
        backend._listener(connection=MagicMock(), pid=1, payload=b"abc", channel="foo")


async def test_asyncpg_backend_publish_before_startup_raises() -> None:
    backend = AsyncPgChannelsBackend(make_connection=AsyncMock())

    with pytest.raises(RuntimeError):
        await backend.publish(b"foo", ["bar"])


async def test_asyncpg_backend_stream_before_startup_raises() -> None:
    backend = AsyncPgChannelsBackend(make_connection=AsyncMock())

    with pytest.raises(RuntimeError):
        await asyncio.wait_for(async_next(backend.stream_events()), timeout=0.01)


async def test_memory_backend_stream_before_startup_raises() -> None:
    backend = MemoryChannelsBackend()

    with pytest.raises(RuntimeError):
        await asyncio.wait_for(async_next(backend.stream_events()), timeout=0.01)
