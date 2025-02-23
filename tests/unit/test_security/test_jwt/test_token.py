from __future__ import annotations

import dataclasses
import secrets
import sys
from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
import pytest
from hypothesis import given
from hypothesis.strategies import datetimes

from litestar.exceptions import ImproperlyConfiguredException, NotAuthorizedException
from litestar.security.jwt import Token
from litestar.security.jwt.token import JWTDecodeOptions


@pytest.mark.parametrize("algorithm", ["HS256", "HS384", "HS512"])
@pytest.mark.parametrize("token_issuer", [None, "e3d7d10edbbc28bfebd8861d39ae7587acde1e1fcefe2cbbec686d235d68f475"])
@pytest.mark.parametrize("token_audience", [None, "627224198b4245ed91cf8353e4ccdf1650728c7ee92748f55fe1e9a9c4d961df"])
@pytest.mark.parametrize(
    "token_unique_jwt_id", [None, "10f5c6967783ddd6bb0c4e8262d7097caeae64705e45f83275e3c32eee5d30f2"]
)
@pytest.mark.parametrize("token_extras", [None, {"email": "test@test.com"}])
def test_token(
    algorithm: str,
    token_issuer: str | None,
    token_audience: str | None,
    token_unique_jwt_id: str | None,
    token_extras: dict[str, Any] | None,
) -> None:
    token_secret = secrets.token_hex()
    token = Token(
        sub=secrets.token_hex(),
        exp=(datetime.now(timezone.utc) + timedelta(minutes=30)),
        aud=token_audience,
        iss=token_issuer,
        jti=token_unique_jwt_id,
        extras=token_extras or {},
    )
    encoded_token = token.encode(secret=token_secret, algorithm=algorithm)
    decoded_token = token.decode(encoded_token=encoded_token, secret=token_secret, algorithm=algorithm)
    assert asdict(token) == asdict(decoded_token)


@pytest.mark.parametrize(
    "algorithm, secret",
    [
        (
            "nope",
            "1",
        ),
        (
            "HS256",
            "",
        ),
        (
            None,
            None,
        ),
        (
            "HS256",
            None,
        ),
        (
            "",
            None,
        ),
        (
            "",
            "",
        ),
        (
            "",
            "1",
        ),
    ],
)
def test_encode_validation(algorithm: str, secret: str) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        Token(
            sub="123",
            exp=(datetime.now(timezone.utc) + timedelta(seconds=30)),
        ).encode(algorithm="nope", secret=secret)


def test_decode_validation() -> None:
    token = Token(
        sub="123",
        exp=(datetime.now(timezone.utc) + timedelta(seconds=30)),
    )
    algorithm = "HS256"
    secret = uuid4().hex
    encoded_token = token.encode(algorithm=algorithm, secret=secret)

    token.decode(encoded_token=encoded_token, algorithm=algorithm, secret=secret)

    with pytest.raises(NotAuthorizedException):
        token.decode(encoded_token=secret, algorithm=algorithm, secret=secret)

    with pytest.raises(NotAuthorizedException):
        token.decode(encoded_token=encoded_token, algorithm="nope", secret=secret)

    with pytest.raises(NotAuthorizedException):
        token.decode(encoded_token=encoded_token, algorithm=algorithm, secret=uuid4().hex)


@given(exp=datetimes(min_value=datetime(1970, 1, 1), max_value=datetime.now() - timedelta(seconds=1)))
def test_exp_validation(exp: datetime) -> None:
    if sys.platform == "win32" and exp == datetime(1970, 1, 1):
        # this does not work on windows. see https://bugs.python.org/issue29097
        pytest.skip("Skipping because .timestamp is weird on windows sometimes")

    with pytest.raises(ImproperlyConfiguredException):
        Token(
            sub="123",
            exp=exp,
            iat=(datetime.now() - timedelta(seconds=30)),
        )


@given(iat=datetimes(min_value=datetime.now() + timedelta(days=1)))
def test_iat_validation(iat: datetime) -> None:
    if sys.platform == "win32" and iat >= datetime(3000, 1, 1, 0, 0):
        # this does not work on windows. see https://bugs.python.org/issue29097
        pytest.skip("Skipping because .timestamp is weird on windows sometimes")

    with pytest.raises(ImproperlyConfiguredException):
        Token(
            sub="123",
            iat=iat,
            exp=(iat + timedelta(seconds=120)),
        )


def test_sub_validation() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        Token(
            sub="",
            iat=(datetime.now() - timedelta(seconds=30)),
            exp=(datetime.now() + timedelta(seconds=120)),
        )


def test_extra_fields() -> None:
    raw_token = {
        "sub": secrets.token_hex(),
        "iat": datetime.now(timezone.utc),
        "azp": "extra value",
        "email": "thetest@test.com",
        "exp": (datetime.now(timezone.utc) + timedelta(seconds=30)),
    }
    token_secret = secrets.token_hex()
    encoded_token = jwt.encode(payload=raw_token, key=token_secret, algorithm="HS256")
    token = Token.decode(encoded_token=encoded_token, secret=token_secret, algorithm="HS256")
    assert "azp" in token.extras
    assert "email" in token.extras

    raw_token = {
        "sub": secrets.token_hex(),
        "iat": datetime.now(timezone.utc),
        "exp": (datetime.now(timezone.utc) + timedelta(seconds=30)),
    }
    token_secret = secrets.token_hex()
    encoded_token = jwt.encode(payload=raw_token, key=token_secret, algorithm="HS256")
    token = Token.decode(encoded_token=encoded_token, secret=token_secret, algorithm="HS256")
    assert token.extras == {}


@pytest.mark.parametrize("audience", [None, ["foo", "bar"]])
def test_strict_aud_with_multiple_audiences_raises(audience: str | list[str]) -> None:
    with pytest.raises(ValueError, match="When using 'strict_audience=True'"):
        Token.decode(
            "",
            secret="",
            algorithm="HS256",
            audience=audience,
            strict_audience=True,
        )


@pytest.mark.parametrize("audience", ["foo", ["foo", "bar"]])
def test_strict_aud_with_one_element_sequence(audience: str | list[str]) -> None:
    # when validating with strict audience, PyJWT requires that the 'audience' parameter
    # is passed as a string - one element lists are not allowed. Since we allow these
    # generally, we convert them to a string in this case
    secret = secrets.token_hex()
    encoded = Token(exp=datetime.now() + timedelta(days=1), sub="foo", aud="foo").encode(secret, "HS256")
    Token.decode(
        encoded,
        secret=secret,
        algorithm="HS256",
        audience=["foo"],
        strict_audience=True,
    )


def test_custom_decode_payload() -> None:
    @dataclasses.dataclass
    class CustomToken(Token):
        @classmethod
        def decode_payload(
            cls,
            encoded_token: str,
            secret: str,
            algorithms: list[str],
            issuer: list[str] | None = None,
            audience: str | Sequence[str] | None = None,
            options: JWTDecodeOptions | None = None,
        ) -> Any:
            payload = super().decode_payload(
                encoded_token=encoded_token,
                secret=secret,
                algorithms=algorithms,
            )
            payload["sub"] = "some-random-value"
            return payload

    _secret = secrets.token_hex()
    encoded = CustomToken(exp=datetime.now() + timedelta(days=1), sub="foo").encode(_secret, "HS256")
    assert CustomToken.decode(encoded, secret=_secret, algorithm="HS256").sub == "some-random-value"
