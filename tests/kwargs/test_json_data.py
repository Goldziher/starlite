from starlite import Body, post
from starlite.status_codes import HTTP_201_CREATED
from starlite.testing import create_test_client
from tests.kwargs import Form


def test_request_body_json() -> None:
    @post(path="/test")
    def test_method(data: Form = Body()) -> None:
        assert isinstance(data, Form)

    with create_test_client(test_method) as client:
        response = client.post("/test", json=Form(name="Moishe Zuchmir", age=30, programmer=True).dict())
        assert response.status_code == HTTP_201_CREATED


def test_empty_dict_allowed() -> None:
    @post(path="/test")
    def test_method(data: dict) -> None:
        assert isinstance(data, dict)

    with create_test_client(test_method) as client:
        response = client.post("/test", json={})
        assert response.status_code == HTTP_201_CREATED
