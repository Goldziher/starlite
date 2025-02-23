from typing import Annotated

from msgspec import Struct

from litestar import post
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.serialization import encode_msgpack
from litestar.status_codes import HTTP_201_CREATED
from litestar.testing import create_test_client


def test_request_body_msgpack() -> None:
    test_data = {"name": "Moishe Zuchmir", "age": 30, "programmer": True}

    @post(path="/header")
    def test_header(data: dict) -> None:
        assert isinstance(data, dict)
        assert data == test_data

    @post(path="/annotated")
    def test_annotated(data: dict = Body(media_type=RequestEncodingType.MESSAGEPACK)) -> None:
        assert isinstance(data, dict)
        assert data == test_data

    with create_test_client([test_header, test_annotated]) as client:
        response = client.post("/annotated", content=encode_msgpack(test_data))
        assert response.status_code == HTTP_201_CREATED


def test_no_body_with_default() -> None:
    class Test(Struct, frozen=True):
        name: str

    default = Test(name="default")

    @post(path="/test", signature_types=[Test])
    def test_method(data: Annotated[Test, Body(media_type=RequestEncodingType.MESSAGEPACK)] = default) -> Test:
        return data

    with create_test_client(test_method) as client:
        response = client.post("/test")
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == {"name": "default"}
