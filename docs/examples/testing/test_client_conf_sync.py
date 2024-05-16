from typing import TYPE_CHECKING, Iterator

import pytest
from my_app.main import app

from litestar.testing import TestClient

if TYPE_CHECKING:
    from litestar import Litestar


@pytest.fixture(scope="function")
def test_client() -> Iterator[TestClient[Litestar]]:
    with TestClient(app=app) as client:
        yield client
