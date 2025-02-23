"""
Test the app running in a subprocess
"""

import asyncio
import pathlib
import sys
from collections.abc import AsyncIterator

import httpx
import httpx_sse
import pytest

from litestar.testing import subprocess_async_client

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


ROOT = pathlib.Path(__file__).parent


@pytest.fixture(name="async_client")
async def fx_async_client() -> AsyncIterator[httpx.AsyncClient]:
    async with subprocess_async_client(workdir=ROOT, app="subprocess_sse_app:app") as client:
        yield client


async def test_subprocess_async_client(async_client: httpx.AsyncClient) -> None:
    """Demonstrates functionality of the async client with an infinite SSE source that cannot be tested with the
    regular async test client.
    """
    topic = "demo"

    async with httpx_sse.aconnect_sse(async_client, "GET", f"/notify/{topic}") as event_source:
        async for event in event_source.aiter_sse():
            assert event.data == topic
            break
