from __future__ import annotations

import msgspec
import pytest
from typing_extensions import Annotated

from litestar import Litestar, get, post
from litestar.datastructures.secret_values import SecretBytes, SecretString
from litestar.openapi.spec.parameter import Parameter as OpenAPIParameter
from litestar.openapi.spec.schema import Schema
from litestar.params import Parameter
from litestar.serialization import default_deserializer, default_serializer
from litestar.testing import create_test_client


def test_secret_string_get_secret() -> None:
    secret_string = SecretString("some_secret_value")
    assert secret_string.get_secret() == "some_secret_value"


def test_secret_string_get_obscured_representation() -> None:
    secret_string = SecretString("some_secret_value")
    assert secret_string.get_obscured() == "******"


def test_secret_string_str() -> None:
    secret_string = SecretString("some_secret_value")
    assert str(secret_string) == "******"


def test_secret_string_repr() -> None:
    secret_string = SecretString("some_secret_value")
    assert repr(secret_string) == "SecretString('******')"


def test_secret_bytes_get_secret() -> None:
    secret_bytes = SecretBytes(b"some_secret_value")
    assert secret_bytes.get_secret() == b"some_secret_value"


def test_secret_bytes_get_obscured_representation() -> None:
    secret_bytes = SecretBytes(b"some_secret_value")
    assert secret_bytes.get_obscured() == b"******"


def test_secret_bytes_str() -> None:
    secret_bytes = SecretBytes(b"some_secret_value")
    assert str(secret_bytes) == str(b"******")


def test_secret_bytes_repr() -> None:
    secret_bytes = SecretBytes(b"some_secret_value")
    assert repr(secret_bytes) == "SecretBytes(b'******')"


def test_secret_string_encode() -> None:
    secret_string = SecretString("some_secret")
    assert default_serializer(secret_string) == "******"


def test_secret_bytes_encode() -> None:
    secret_bytes = SecretBytes(b"some_secret")
    assert default_serializer(secret_bytes) == "******"


def test_secret_string_decode() -> None:
    secret = default_deserializer(SecretString, "super-secret")
    assert isinstance(secret, SecretString)
    assert secret.get_secret() == "super-secret"


def test_secret_bytes_decode() -> None:
    secret = default_deserializer(SecretBytes, b"super-secret")
    assert isinstance(secret, SecretBytes)
    assert secret.get_secret() == b"super-secret"


def test_secret_string_parameter() -> None:
    @get()
    def get_secret(secret: SecretString) -> SecretBytes:
        assert secret.get_secret() == "super-secret"
        return SecretBytes(b"super-secret")

    with create_test_client([get_secret]) as client:
        response = client.get("/?secret=super-secret")
        assert response.status_code == 200
        assert response.json() == "******"


def test_decode_secret_string_on_model() -> None:
    class Model(msgspec.Struct):
        secret: SecretString

    @post(signature_types=[Model])
    async def post_secret(data: Model) -> None:
        assert data.secret.get_secret() == "super"

    with create_test_client([post_secret]) as client:
        response = client.post("/", json={"secret": "super"})
        assert response.status_code == 201


def test_decode_secret_bytes_on_model() -> None:
    class Model(msgspec.Struct):
        secret: SecretBytes

    @post(signature_types=[Model])
    async def post_secret(data: Model) -> None:
        assert data.secret.get_secret() == b"super"

    with create_test_client([post_secret]) as client:
        response = client.post("/", json={"secret": "super"})
        assert response.status_code == 201


@pytest.mark.parametrize(("secret_type",), [(SecretString,), (SecretBytes,)])
def test_decode_secret_string_on_model_client_error(secret_type: type[SecretString | SecretBytes]) -> None:
    model = msgspec.defstruct(name="Model", fields=[("secret", secret_type)])

    @post(signature_namespace={"model": model})
    async def post_secret(data: model) -> None:  # type: ignore[valid-type]
        return None

    with create_test_client([post_secret]) as client:
        response = client.post("/", json={"secret": 123})
        assert response.status_code == 400
        assert response.json() == {
            "status_code": 400,
            "detail": "Validation failed for POST /",
            "extra": [{"message": "Unsupported type: <class 'int'>", "key": "secret", "source": "body"}],
        }


def test_secret_openapi() -> None:
    @get(sync_to_thread=False)
    def get_secret(secret: Annotated[SecretString, Parameter(header="x-secret")]) -> str:
        return secret.get_obscured()

    app = Litestar(route_handlers=[get_secret])
    paths = app.openapi_schema.paths
    assert paths is not None
    op = paths["/"].get
    assert op is not None
    assert op.parameters is not None
    param = op.parameters[0]
    assert isinstance(param, OpenAPIParameter)
    assert param.name == "x-secret"
    assert param.param_in == "header"
    assert isinstance(param.schema, Schema)
    assert param.schema.type == "string"


def test_secret_value_in_model_repr() -> None:
    class Model(msgspec.Struct):
        string: SecretString
        bytes: SecretBytes

    model = Model(string=SecretString("super-secret"), bytes=SecretBytes(b"super-secret"))
    assert repr(model) == "Model(string=SecretString('******'), bytes=SecretBytes(b'******'))"
    assert str(model) == "Model(string=SecretString('******'), bytes=SecretBytes(b'******'))"
