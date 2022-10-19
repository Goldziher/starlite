from starlette.status import HTTP_200_OK

from examples.dependency_injection import dependency_skip_validation
from starlite.testing import TestClient


def test_route_returns_internal_server_error() -> None:
    with TestClient(app=dependency_skip_validation.app) as client:
        r = client.get("/")
    assert r.status_code == HTTP_200_OK
