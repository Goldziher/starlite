from examples.application_state.passing_initial_state import app
from starlite import TestClient
from starlite.status_codes import HTTP_200_OK


def test_passing_initial_state_example() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"count": 100}
