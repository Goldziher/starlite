from collections.abc import AsyncIterator

import pytest

from litestar import Litestar, MediaType, get
from litestar.status_codes import HTTP_200_OK
from litestar.testing import AsyncTestClient


@get(path="/health-check", media_type=MediaType.TEXT, sync_to_thread=False)
def health_check() -> str:
    return "healthy"


app = Litestar(route_handlers=[health_check], debug=True)


@pytest.fixture(scope="function")
async def test_client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    async with AsyncTestClient(app=app) as client:
        yield client


async def test_health_check_with_fixture(test_client: AsyncTestClient[Litestar]) -> None:
    response = await test_client.get("/health-check")
    assert response.status_code == HTTP_200_OK
    assert response.text == "healthy"
