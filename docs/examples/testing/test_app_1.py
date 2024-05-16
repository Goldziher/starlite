from my_app.main import health_check

from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


def test_health_check():
    with create_test_client(route_handlers=[health_check]) as client:
        response = client.get("/health-check")
        assert response.status_code == HTTP_200_OK
        assert response.text == "healthy"
