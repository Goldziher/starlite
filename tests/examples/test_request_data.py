from docs.examples.request_data.custom_request import app as custom_request_class_app
from docs.examples.request_data.msgpack_request import app as msgpack_app
from docs.examples.request_data.request_data_1 import app
from docs.examples.request_data.request_data_2 import app as app_2
from docs.examples.request_data.request_data_3 import app as app_3
from docs.examples.request_data.request_data_4 import app as app_4
from docs.examples.request_data.request_data_5 import app as app_5
from docs.examples.request_data.request_data_6 import app as app_6
from docs.examples.request_data.request_data_7 import app as app_7
from docs.examples.request_data.request_data_8 import app as app_8
from docs.examples.request_data.request_data_9 import app as app_9
from docs.examples.request_data.request_data_10 import app as app_10

from litestar.serialization import encode_msgpack
from litestar.testing import TestClient


def test_request_data_1() -> None:
    with TestClient(app=app) as client:
        response = client.post("/", json={"hello": "world"})
        assert response.status_code == 201
        assert response.json() == {"hello": "world"}


def test_request_data_2() -> None:
    with TestClient(app=app_2) as client:
        response = client.post("/", json={"id": 1, "name": "John"})
        assert response.status_code == 201
        assert response.json() == {"id": 1, "name": "John"}


def test_request_data_3() -> None:
    with TestClient(app=app_3) as client:
        response = client.post("/", json={"id": 1, "name": "John"})
        assert response.status_code == 201
        assert response.json() == {"id": 1, "name": "John"}


def test_request_data_4() -> None:
    with TestClient(app=app_4) as client:
        response = client.post("/", data={"id": 1, "name": "John"})
        assert response.status_code == 201
        assert response.json() == {"id": 1, "name": "John"}


def test_request_data_5() -> None:
    with TestClient(app=app_5) as client:
        response = client.post(
            "/",
            content=b'--d26a9a4ed2f441fba9ab42d04b42099e\r\nContent-Disposition: form-data; name="id"\r\n\r\n1\r\n--d26a9a4ed2f441fba9ab42d04b42099e\r\nContent-Disposition: form-data; name="name"\r\n\r\nJohn\r\n--d26a9a4ed2f441fba9ab42d04b42099e--\r\n',
            headers={
                "Content-Length": "211",
                "Content-Type": "multipart/form-data; boundary=d26a9a4ed2f441fba9ab42d04b42099e",
            },
        )
        assert response.json() == {"id": 1, "name": "John"}
        assert response.status_code == 201


def test_request_data_6() -> None:
    with TestClient(app=app_6) as client:
        response = client.post("/", files={"upload": ("hello", b"world")})
        assert response.status_code == 201
        assert response.text == "hello, world"


def test_request_data_7() -> None:
    with TestClient(app=app_7) as client:
        response = client.post("/", files={"upload": ("hello", b"world")})
        assert response.status_code == 201
        assert response.text == "hello, world"


def test_request_data_8() -> None:
    with TestClient(app=app_8) as client:
        response = client.post(
            "/", files={"cv": ("cv.odf", b"very impressive"), "diploma": ("diploma.pdf", b"the best")}
        )
        assert response.status_code == 201
        assert response.json() == {"cv": "very impressive", "diploma": "the best"}


def test_request_data_9() -> None:
    with TestClient(app=app_9) as client:
        response = client.post("/", files={"hello": b"there", "i'm": "steve"})
        assert response.status_code == 201
        assert response.json() == {"hello": "there", "i'm": "steve"}


def test_request_data_10() -> None:
    with TestClient(app=app_10) as client:
        response = client.post("/", files={"foo": ("foo.txt", b"hello"), "bar": ("bar.txt", b"world")})
        assert response.status_code == 201
        assert response.json() == {"foo.txt": "hello", "bar.txt": "world"}


def test_msgpack_app() -> None:
    test_data = {"name": "Moishe Zuchmir", "age": 30, "programmer": True}

    with TestClient(app=msgpack_app) as client:
        response = client.post("/", content=encode_msgpack(test_data))
        assert response.json() == test_data


def test_custom_request_app() -> None:
    with TestClient(app=custom_request_class_app) as client:
        response = client.get("/kitten-name")
        assert response.content == b"Whiskers"
