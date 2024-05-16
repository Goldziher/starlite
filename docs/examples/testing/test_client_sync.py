from my_app.main import app

from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient


def test_health_check():
    with TestClient(app=app) as client:
        response = client.get("/health-check")
        assert response.status_code == HTTP_200_OK
        assert response.text == "healthy"
