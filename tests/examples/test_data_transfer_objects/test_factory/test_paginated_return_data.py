from litestar.status_codes import HTTP_200_OK
from litestar.testing.client import TestClient


def test_create_user() -> None:
    from docs.examples.data_transfer_objects.factory.paginated_return_data import app

    with TestClient(app=app) as client:
        response = client.get("/users")

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "current_page": 1,
        "items": [{"id": 1, "name": "Litestar User"}],
        "page_size": 10,
        "total_pages": 1,
    }
