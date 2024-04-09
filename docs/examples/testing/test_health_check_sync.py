from typing import Iterator

import pytest

from litestar import Litestar, MediaType, get
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient


@get(path="/health-check", media_type=MediaType.TEXT, sync_to_thread=False)
def health_check() -> str:
    return "healthy"


app = Litestar(route_handlers=[health_check])


def test_health_check() -> None:
    with TestClient(app=app) as client:
        response = client.get("/health-check")
        assert response.status_code == HTTP_200_OK
        assert response.text == "healthy"


@pytest.fixture(scope="function")
def test_client() -> Iterator[TestClient[Litestar]]:
    with TestClient(app=app) as client:
        yield client


def test_health_check_with_fixture(test_client: TestClient[Litestar]) -> None:
    response = test_client.get("/health-check")
    assert response.status_code == HTTP_200_OK
    assert response.text == "healthy"
