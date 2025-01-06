from typing import AsyncGenerator

import pytest

from litestar.utils.compat import async_next


@pytest.mark.anyio
async def test_async_next() -> None:
    async def generator() -> AsyncGenerator:
        yield 1

    gen = generator()

    assert await async_next(gen) == 1
    assert await async_next(gen, None) is None
    with pytest.raises(StopAsyncIteration):
        await async_next(gen)
