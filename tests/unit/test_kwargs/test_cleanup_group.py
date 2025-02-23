from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest

from litestar._kwargs.cleanup import DependencyCleanupGroup
from litestar.utils.compat import async_next


@pytest.fixture
def cleanup_mock() -> MagicMock:
    return MagicMock()


@pytest.fixture
def async_cleanup_mock() -> MagicMock:
    return MagicMock()


@pytest.fixture
def generator(cleanup_mock: MagicMock) -> Generator[str, None, None]:
    def func() -> Generator[str, None, None]:
        yield "hello"
        cleanup_mock()

    return func()


@pytest.fixture
def async_generator(async_cleanup_mock: MagicMock) -> AsyncGenerator[str, None]:
    async def func() -> AsyncGenerator[str, None]:
        yield "world"
        async_cleanup_mock()

    return func()


def test_add(generator: Generator[str, None, None]) -> None:
    group = DependencyCleanupGroup()

    group.add(generator)

    assert group._generators == [generator]


async def test_cleanup(generator: Generator[str, None, None], cleanup_mock: MagicMock) -> None:
    next(generator)
    group = DependencyCleanupGroup([generator])

    await group.cleanup()

    cleanup_mock.assert_called_once()
    assert group._closed


async def test_cleanup_multiple(
    generator: Generator[str, None, None],
    async_generator: AsyncGenerator[str, None],
    cleanup_mock: MagicMock,
    async_cleanup_mock: MagicMock,
) -> None:
    next(generator)
    await async_next(async_generator)
    group = DependencyCleanupGroup([generator, async_generator])

    await group.cleanup()

    cleanup_mock.assert_called_once()
    async_cleanup_mock.assert_called_once()
    assert group._closed


async def test_cleanup_on_closed_raises(generator: Generator[str, None, None]) -> None:
    next(generator)
    group = DependencyCleanupGroup([generator])

    await group.cleanup()
    with pytest.raises(RuntimeError):
        await group.cleanup()


async def test_add_on_closed_raises(
    generator: Generator[str, None, None], async_generator: AsyncGenerator[str, None]
) -> None:
    next(generator)
    group = DependencyCleanupGroup([generator])

    await group.cleanup()

    with pytest.raises(RuntimeError):
        group.add(async_generator)
