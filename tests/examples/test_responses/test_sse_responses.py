import pytest
from docs.examples.responses.sse_responses import app
from httpx_sse import aconnect_sse

from litestar.testing import AsyncTestClient


@pytest.mark.anyio
async def test_sse_responses_example() -> None:
    async with AsyncTestClient(app=app) as client:
        async with aconnect_sse(client, "GET", f"{client.base_url}/count") as event_source:
            events = [sse async for sse in event_source.aiter_sse()]
            assert len(events) == 50
