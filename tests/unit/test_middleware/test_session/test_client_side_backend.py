import os
import secrets
import time
from base64 import b64decode, b64encode
from typing import Any, Dict
from unittest import mock

import pytest
from cryptography.exceptions import InvalidTag

from litestar import Request, get, post
from litestar.exceptions import ImproperlyConfiguredException
from litestar.middleware.session import SessionMiddleware
from litestar.middleware.session.client_side import (
    AAD,
    CHUNK_SIZE,
    ClientSideSessionBackend,
    CookieBackendConfig,
)
from litestar.serialization import encode_json
from litestar.testing import create_test_client
from tests.helpers import randbytes


@pytest.mark.parametrize(
    "secret, should_raise",
    [
        [randbytes(16), False],
        [randbytes(24), False],
        [randbytes(32), False],
        [randbytes(17), True],
        [randbytes(4), True],
        [randbytes(100), True],
        [b"", True],
    ],
)
def test_secret_validation(secret: bytes, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            CookieBackendConfig(secret=secret)
    else:
        CookieBackendConfig(secret=secret)


@pytest.mark.parametrize(
    "key, should_raise",
    [
        ["", True],
        ["a", False],
        ["a" * 256, False],
        ["a" * 257, True],
    ],
)
def test_key_validation(key: str, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            CookieBackendConfig(secret=os.urandom(16), key=key)
    else:
        CookieBackendConfig(secret=os.urandom(16), key=key)


@pytest.mark.parametrize(
    "max_age, should_raise",
    [
        [0, True],
        [-1, True],
        [1, False],
        [100, False],
    ],
)
def test_max_age_validation(max_age: int, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            CookieBackendConfig(secret=os.urandom(16), key="a", max_age=max_age)
    else:
        CookieBackendConfig(secret=os.urandom(16), key="a", max_age=max_age)


def create_session(size: int = 16) -> Dict[str, str]:
    return {"key": secrets.token_hex(size)}


@pytest.mark.parametrize("session", [create_session(), create_session(size=4096)])
def test_dump_and_load_data(session: dict, cookie_session_backend: ClientSideSessionBackend) -> None:
    ciphertext = cookie_session_backend.dump_data(session)
    assert isinstance(ciphertext, list)

    for text in ciphertext:
        assert len(text) <= CHUNK_SIZE

    plain_text = cookie_session_backend.load_data(ciphertext)
    assert plain_text == session


@mock.patch("time.time", return_value=round(time.time()))
def test_load_data_should_return_empty_if_session_expired(
    time_mock: mock.MagicMock, cookie_session_backend: ClientSideSessionBackend
) -> None:
    """Should return empty dict if session is expired."""
    ciphertext = cookie_session_backend.dump_data(create_session())
    time_mock.return_value = round(time.time()) + cookie_session_backend.config.max_age + 1
    plaintext = cookie_session_backend.load_data(data=ciphertext)
    assert plaintext == {}


def test_set_session_cookies(cookie_session_backend_config: "CookieBackendConfig") -> None:
    """Should set session cookies from session in response."""
    chunks_multiplier = 2

    @get(path="/test")
    def handler(request: Request) -> None:
        # Create large session by keeping it multiple of CHUNK_SIZE. This will split the session into multiple cookies.
        # Then you only need to check if number of cookies set are more than the multiplying number.
        request.session.update(create_session(size=CHUNK_SIZE * chunks_multiplier))

    @get(path="/test_short_cookie")
    def handler_short_cookie(request: Request) -> None:
        # Check the naming of a cookie that's short enough to not get broken into chunks
        request.session.update(create_session())

    with create_test_client(
        route_handlers=[handler],
        middleware=[cookie_session_backend_config.middleware],
    ) as client:
        response = client.get("/test")

        assert len(response.cookies) > chunks_multiplier
        assert "session-0" in response.cookies

    with create_test_client(
        route_handlers=[handler_short_cookie],
        middleware=[cookie_session_backend_config.middleware],
    ) as client:
        response = client.get("/test_short_cookie")

        assert len(response.cookies) == 1
        assert "session" in response.cookies


def test_session_cookie_name_matching(cookie_session_backend_config: "CookieBackendConfig") -> None:
    session_data = {"foo": "bar"}

    @get("/")
    def handler(request: Request) -> Dict[str, Any]:
        return request.session

    @post("/")
    def set_session_data(request: Request) -> None:
        request.set_session(session_data)

    with create_test_client(
        route_handlers=[handler, set_session_data],
        middleware=[cookie_session_backend_config.middleware],
    ) as client:
        client.post("/")
        client.cookies[f"thisisnnota{cookie_session_backend_config.key}cookie"] = "foo"
        response = client.get("/")
        assert response.json() == session_data


@pytest.mark.parametrize("mutate", [False, True])
def test_load_session_cookies_and_expire_previous(
    mutate: bool, cookie_session_middleware: SessionMiddleware[ClientSideSessionBackend]
) -> None:
    """Should load session cookies into session from request and overwrite the previously set cookies with the upcoming
    response.

    Session cookies from the previous session should not persist because session is mutable. Once the session is loaded
    from the cookies, those cookies are redundant. The response sets new session cookies overwriting or expiring the
    previous ones.
    """
    # Test for large session data. If it works for multiple cookies, it works for single also.
    _session = create_session(size=4096)

    @get(path="/test")
    def handler(request: Request) -> dict:
        nonlocal _session
        if mutate:
            # Modify the session, this will overwrite the previously set session cookies.
            request.session.update(create_session())
            _session = request.session
        return request.session

    ciphertext = cookie_session_middleware.backend.dump_data(_session)

    with create_test_client(
        route_handlers=[handler],
        middleware=[cookie_session_middleware.backend.config.middleware],
    ) as client:
        # Set cookies on the client to avoid warnings about per-request cookies.
        client.cookies = {  # type: ignore[assignment]
            f"{cookie_session_middleware.backend.config.key}-{i}": text.decode("utf-8")
            for i, text in enumerate(ciphertext)
        }
        response = client.get("/test")

    assert response.json() == _session
    # The session cookie names that were in the request will also be present in its response to overwrite or to expire
    # them. So, the number of cookies in the response will be at least equal to or greater than the number of cookies
    # that were in the request.
    assert response.headers["set-cookie"].count("session") >= response.request.headers["Cookie"].count("session")


def test_load_data_should_raise_invalid_tag_if_tampered_aad(cookie_session_backend: ClientSideSessionBackend) -> None:
    """If AAD has been tampered with, the integrity of the data cannot be verified and InavlidTag exception is
    raised.
    """
    encrypted_session = cookie_session_backend.dump_data(create_session())
    # The attacker will tamper with the AAD to increase the expiry time of the cookie.
    attacker_chosen_time = 300  # In seconds
    fraudulent_associated_data = encode_json(
        {"expires_at": round(time.time()) + cookie_session_backend.config.max_age + attacker_chosen_time}
    )
    decoded = b64decode(b"".join(encrypted_session))
    aad_starts_from = decoded.find(AAD)
    # The attacker removes the original AAD and attaches its own.
    ciphertext = b64encode(decoded[:aad_starts_from] + AAD + fraudulent_associated_data)
    # The attacker puts the data back to its original form.
    encoded = [ciphertext[i : i + CHUNK_SIZE] for i in range(0, len(ciphertext), CHUNK_SIZE)]

    with pytest.raises(InvalidTag):
        cookie_session_backend.load_data(encoded)
