from docs.examples.datastructures.secrets.secret_body import post_handler
from docs.examples.datastructures.secrets.secret_header import get_handler

from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from litestar.testing import create_test_client


def test_secret_header() -> None:
    with create_test_client(get_handler) as client:
        r = client.get("/", headers={"x-secret": "super-secret"})

    assert r.status_code == HTTP_200_OK
    assert r.json() == {"value": "sensitive data"}


def test_secret_body() -> None:
    with create_test_client(post_handler) as client:
        r = client.post("/", json={"value": "super-secret"})

    assert r.status_code == HTTP_201_CREATED
    assert r.json() == {"value": "******"}
