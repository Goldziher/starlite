"""
Test the app running in a subprocess
"""

import asyncio
import pathlib
import sys
from typing import AsyncIterator, Iterator

import httpx
import httpx_sse
import pytest

from litestar.testing import subprocess_async_client, subprocess_sync_client

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


ROOT = pathlib.Path(__file__).parent


@pytest.fixture(name="async_client", scope="session")
async def fx_async_client() -> AsyncIterator[httpx.AsyncClient]:
    async with subprocess_async_client(workdir=ROOT, app="demo:app") as client:
        yield client


@pytest.fixture(name="sync_client", scope="session")
def fx_sync_client() -> Iterator[httpx.Client]:
    with subprocess_sync_client(workdir=ROOT, app="demo:app") as client:
        yield client


@pytest.mark.anyio
async def test_subprocess_async_client(async_client: httpx.AsyncClient) -> None:
    """Demonstrates functionality of the async client with an infinite SSE source that cannot be tested with the
    regular async test client.
    """

    async with httpx_sse.aconnect_sse(async_client, "GET", "/notify/hello") as event_source:
        async for event in event_source.aiter_sse():
            assert event.data == "hello"
            break


def test_subprocess_sync_client(sync_client: httpx.Client) -> None:
    """Demonstrates functionality of the async client with an infinite SSE source that cannot be tested with the
    regular async test client.
    """

    with httpx_sse.connect_sse(sync_client, "GET", "/notify/hello") as event_source:
        for event in event_source.iter_sse():
            assert event.data == "hello"
            break
