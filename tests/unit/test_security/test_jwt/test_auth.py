import string
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import uuid4

import msgspec
import pytest
from hypothesis import given, settings
from hypothesis.strategies import dictionaries, integers, none, one_of, sampled_from, text, timedeltas

from litestar import Litestar, Request, Response, get
from litestar.security.jwt import JWTAuth, JWTCookieAuth, OAuth2PasswordBearerAuth, Token
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.stores.memory import MemoryStore
from litestar.testing import create_test_client
from tests.models import User, UserFactory

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection


@pytest.fixture(scope="module")
def mock_db() -> MemoryStore:
    return MemoryStore()


@given(
    algorithm=sampled_from(
        [
            "HS256",
            "HS384",
            "HS512",
        ]
    ),
    auth_header=sampled_from(["Authorization", "X-API-Key"]),
    default_token_expiration=timedeltas(min_value=timedelta(seconds=30), max_value=timedelta(weeks=1)),
    token_secret=text(min_size=10),
    response_status_code=integers(min_value=200, max_value=201),
    token_expiration=timedeltas(min_value=timedelta(seconds=30), max_value=timedelta(weeks=1)),
    token_issuer=one_of(none(), text(max_size=256)),
    token_audience=one_of(none(), text(max_size=256, alphabet=string.ascii_letters)),
    token_unique_jwt_id=one_of(none(), text(max_size=256)),
    token_extras=one_of(none(), dictionaries(text(max_size=256), text(max_size=256))),
)
@settings(deadline=None)
async def test_jwt_auth(
    mock_db: "MemoryStore",
    algorithm: str,
    auth_header: str,
    default_token_expiration: timedelta,
    token_secret: str,
    response_status_code: int,
    token_expiration: timedelta,
    token_issuer: Optional[str],
    token_audience: Optional[str],
    token_unique_jwt_id: Optional[str],
    token_extras: Optional[Dict[str, Any]],
) -> None:
    user = UserFactory.build()

    await mock_db.set(str(user.id), user, 120)  # type: ignore[arg-type]

    async def retrieve_user_handler(token: Token, _: "ASGIConnection") -> Any:
        return await mock_db.get(token.sub)

    jwt_auth = JWTAuth[Any](
        algorithm=algorithm,
        auth_header=auth_header,
        default_token_expiration=default_token_expiration,
        token_secret=token_secret,
        retrieve_user_handler=retrieve_user_handler,
    )

    @get("/my-endpoint", middleware=[jwt_auth.middleware])
    def my_handler(request: Request["User", Token, Any]) -> None:
        assert request.user
        assert msgspec.to_builtins(request.user) == msgspec.to_builtins(user)
        assert request.auth.sub == str(user.id)

    @get("/login")
    def login_handler() -> Response["User"]:
        return jwt_auth.login(
            identifier=str(user.id),
            response_body=user,
            response_status_code=response_status_code,
            token_expiration=token_expiration,
            token_issuer=token_issuer,
            token_audience=token_audience,
            token_unique_jwt_id=token_unique_jwt_id,
            token_extras=token_extras,
        )

    with create_test_client(route_handlers=[my_handler, login_handler]) as client:
        response = client.get("/login")
        assert response.status_code == response_status_code
        _, _, encoded_token = response.headers.get(auth_header).partition(" ")
        assert encoded_token
        decoded_token = Token.decode(encoded_token=encoded_token, secret=token_secret, algorithm=algorithm)
        assert decoded_token.sub == str(user.id)
        assert decoded_token.iss == token_issuer
        assert decoded_token.aud == token_audience
        assert decoded_token.jti == token_unique_jwt_id
        if token_extras is not None:
            for key, value in token_extras.items():
                assert decoded_token.extras[key] == value

        response = client.get("/my-endpoint")
        assert response.status_code == HTTP_401_UNAUTHORIZED

        response = client.get("/my-endpoint", headers={auth_header: jwt_auth.format_auth_header(encoded_token)})
        assert response.status_code == HTTP_200_OK

        response = client.get("/my-endpoint", headers={auth_header: encoded_token})
        assert response.status_code == HTTP_401_UNAUTHORIZED

        response = client.get("/my-endpoint", headers={auth_header: uuid4().hex})
        assert response.status_code == HTTP_401_UNAUTHORIZED

        fake_token = Token(
            sub=uuid4().hex,
            iss=token_issuer,
            aud=token_audience,
            jti=token_unique_jwt_id,
            exp=(datetime.now(timezone.utc) + token_expiration),
        ).encode(secret=token_secret, algorithm=algorithm)

        response = client.get("/my-endpoint", headers={auth_header: jwt_auth.format_auth_header(fake_token)})
        assert response.status_code == HTTP_401_UNAUTHORIZED


@given(
    algorithm=sampled_from(
        [
            "HS256",
            "HS384",
            "HS512",
        ]
    ),
    auth_header=sampled_from(["Authorization", "X-API-Key"]),
    auth_cookie=sampled_from(["token", "accessToken"]),
    default_token_expiration=timedeltas(min_value=timedelta(seconds=30), max_value=timedelta(weeks=1)),
    token_secret=text(min_size=10),
    response_status_code=integers(min_value=200, max_value=201),
    token_expiration=timedeltas(min_value=timedelta(seconds=30), max_value=timedelta(weeks=1)),
    token_issuer=one_of(none(), text(max_size=256)),
    token_audience=one_of(none(), text(max_size=256, alphabet=string.ascii_letters)),
    token_unique_jwt_id=one_of(none(), text(max_size=256)),
    token_extras=one_of(none(), dictionaries(text(max_size=256), text(max_size=256))),
)
@settings(deadline=None)
async def test_jwt_cookie_auth(
    mock_db: "MemoryStore",
    algorithm: str,
    auth_header: str,
    auth_cookie: str,
    default_token_expiration: timedelta,
    token_secret: str,
    response_status_code: int,
    token_expiration: timedelta,
    token_issuer: Optional[str],
    token_audience: Optional[str],
    token_unique_jwt_id: Optional[str],
    token_extras: Optional[Dict[str, Any]],
) -> None:
    user = UserFactory.build()

    await mock_db.set(str(user.id), user, 120)  # type: ignore[arg-type]

    async def retrieve_user_handler(token: Token, connection: Any) -> Any:
        assert connection
        return await mock_db.get(token.sub)

    jwt_auth = JWTCookieAuth(
        algorithm=algorithm,
        key=auth_cookie,
        auth_header=auth_header,
        default_token_expiration=default_token_expiration,
        retrieve_user_handler=retrieve_user_handler,  # type: ignore[var-annotated]
        token_secret=token_secret,
    )

    @get("/my-endpoint", middleware=[jwt_auth.middleware])
    def my_handler(request: Request["User", Token, Any]) -> None:
        assert request.user
        assert msgspec.to_builtins(request.user) == msgspec.to_builtins(user)
        assert request.auth.sub == str(user.id)

    @get("/login")
    def login_handler() -> Response["User"]:
        return jwt_auth.login(
            identifier=str(user.id),
            response_body=user,
            response_status_code=response_status_code,
            token_expiration=token_expiration,
            token_issuer=token_issuer,
            token_audience=token_audience,
            token_unique_jwt_id=token_unique_jwt_id,
            token_extras=token_extras,
        )

    with create_test_client(route_handlers=[my_handler, login_handler]) as client:
        response = client.get("/login")
        assert response.status_code == response_status_code
        _, _, encoded_token = response.headers.get(auth_header).partition(" ")
        assert encoded_token
        decoded_token = Token.decode(encoded_token=encoded_token, secret=token_secret, algorithm=algorithm)
        assert decoded_token.sub == str(user.id)
        assert decoded_token.iss == token_issuer
        assert decoded_token.aud == token_audience
        assert decoded_token.jti == token_unique_jwt_id
        if token_extras is not None:
            for key, value in token_extras.items():
                assert decoded_token.extras[key] == value

        client.cookies.clear()
        response = client.get("/my-endpoint")
        assert response.status_code == HTTP_401_UNAUTHORIZED

        client.cookies.clear()
        response = client.get("/my-endpoint", headers={auth_header: jwt_auth.format_auth_header(encoded_token)})
        assert response.status_code == HTTP_200_OK

        client.cookies = {auth_cookie: jwt_auth.format_auth_header(encoded_token)}  # type: ignore[assignment]
        response = client.get(
            "/my-endpoint",
        )
        assert response.status_code == HTTP_200_OK

        client.cookies.clear()
        response = client.get("/my-endpoint", headers={auth_header: encoded_token})
        assert response.status_code == HTTP_401_UNAUTHORIZED

        client.cookies.clear()
        response = client.get("/my-endpoint", headers={auth_cookie: encoded_token})
        assert response.status_code == HTTP_401_UNAUTHORIZED

        client.cookies.clear()
        response = client.get("/my-endpoint", headers={auth_header: jwt_auth.format_auth_header(uuid4().hex)})
        assert response.status_code == HTTP_401_UNAUTHORIZED

        client.cookies = {auth_cookie: jwt_auth.format_auth_header(uuid4().hex)}  # type: ignore[assignment]
        response = client.get("/my-endpoint")
        assert response.status_code == HTTP_401_UNAUTHORIZED

        client.cookies = {auth_cookie: uuid4().hex}  # type: ignore[assignment]
        response = client.get("/my-endpoint")
        assert response.status_code == HTTP_401_UNAUTHORIZED
        fake_token = Token(
            sub=uuid4().hex,
            iss=token_issuer,
            aud=token_audience,
            jti=token_unique_jwt_id,
            exp=(datetime.now(timezone.utc) + token_expiration),
        ).encode(secret=token_secret, algorithm=algorithm)

        client.cookies.clear()
        response = client.get("/my-endpoint", headers={auth_header: jwt_auth.format_auth_header(fake_token)})
        assert response.status_code == HTTP_401_UNAUTHORIZED

        client.cookies = {auth_cookie: jwt_auth.format_auth_header(fake_token)}  # type: ignore[assignment]
        response = client.get("/my-endpoint")
        assert response.status_code == HTTP_401_UNAUTHORIZED


async def test_path_exclusion() -> None:
    async def retrieve_user_handler(_: Token, __: "ASGIConnection") -> None:
        return None

    jwt_auth = JWTAuth[Any](
        token_secret="abc123",
        retrieve_user_handler=retrieve_user_handler,
        exclude=["north", "south"],
    )

    @get("/north/{value:int}")
    def north_handler(value: int) -> Dict[str, int]:
        return {"value": value}

    @get("/south")
    def south_handler() -> None:
        return None

    @get("/west")
    def west_handler() -> None:
        return None

    with create_test_client(
        route_handlers=[north_handler, south_handler, west_handler], on_app_init=[jwt_auth.on_app_init]
    ) as client:
        response = client.get("/north/1")
        assert response.status_code == HTTP_200_OK

        response = client.get("/south")
        assert response.status_code == HTTP_200_OK

        response = client.get("/west")
        assert response.status_code == HTTP_401_UNAUTHORIZED


def test_jwt_auth_openapi() -> None:
    jwt_auth = JWTAuth[Any](token_secret="abc123", retrieve_user_handler=lambda _: None)  # type: ignore[arg-type, misc]
    assert jwt_auth.openapi_components.to_schema() == {
        "schemas": {},
        "securitySchemes": {
            "BearerToken": {
                "type": "http",
                "description": "JWT api-key authentication and authorization.",
                "name": "Authorization",
                "scheme": "Bearer",
                "bearerFormat": "JWT",
            }
        },
    }
    assert jwt_auth.security_requirement == {"BearerToken": []}
    app = Litestar(on_app_init=[jwt_auth.on_app_init])

    assert app.openapi_schema
    assert app.openapi_schema.to_schema() == {
        "openapi": "3.1.0",
        "info": {"title": "Litestar API", "version": "1.0.0"},
        "servers": [{"url": "/"}],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "BearerToken": {
                    "type": "http",
                    "description": "JWT api-key authentication and authorization.",
                    "name": "Authorization",
                    "scheme": "Bearer",
                    "bearerFormat": "JWT",
                }
            },
        },
        "security": [{"BearerToken": []}],
    }


async def test_oauth2_password_bearer_auth_openapi(mock_db: "MemoryStore") -> None:
    user = UserFactory.build()

    await mock_db.set(str(user.id), user, 120)  # type: ignore[arg-type]

    async def retrieve_user_handler(token: Token, connection: Any) -> Any:
        assert connection
        return await mock_db.get(token.sub)

    jwt_auth = OAuth2PasswordBearerAuth(
        token_url="/login",
        token_secret="abc123",
        retrieve_user_handler=retrieve_user_handler,  # type: ignore[var-annotated]
    )

    @get("/login")
    def login_handler() -> Response["User"]:
        return jwt_auth.login(identifier=str(user.id))

    @get("/login_custom")
    def login_custom_handler() -> Response["User"]:
        return jwt_auth.login(identifier=str(user.id), response_body=user)

    with create_test_client(route_handlers=[login_custom_handler, login_handler]) as client:
        response = client.get("/login")
        response_custom = client.get("/login_custom")
        assert "access_token" in response.content.decode()
        assert response.content != response_custom.content

    assert jwt_auth.openapi_components.to_schema() == {
        "schemas": {},
        "securitySchemes": {
            "BearerToken": {
                "type": "oauth2",
                "description": "OAUTH2 password bearer authentication and authorization.",
                "name": "Authorization",
                "in": "header",
                "scheme": "Bearer",
                "bearerFormat": "JWT",
                "flows": {"password": {"tokenUrl": "/login"}},
            }
        },
    }

    assert jwt_auth.security_requirement == {"BearerToken": []}

    app = Litestar(on_app_init=[jwt_auth.on_app_init])
    assert app.openapi_schema.to_schema() == {
        "openapi": "3.1.0",
        "info": {"title": "Litestar API", "version": "1.0.0"},
        "servers": [{"url": "/"}],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "BearerToken": {
                    "type": "oauth2",
                    "description": "OAUTH2 password bearer authentication and authorization.",
                    "name": "Authorization",
                    "in": "header",
                    "scheme": "Bearer",
                    "bearerFormat": "JWT",
                    "flows": {"password": {"tokenUrl": "/login"}},
                }
            },
        },
        "security": [{"BearerToken": []}],
    }


def test_type_encoders() -> None:
    # see: https://github.com/litestar-org/litestar/issues/1136

    class CustomUser:
        def __init__(self, id: str) -> None:
            self.id = id

    async def retrieve_user_handler(token: Token, connection: "ASGIConnection[Any, Any, Any, Any]") -> CustomUser:
        return CustomUser(id=token.sub)

    jwt_cookie_auth = JWTCookieAuth[User](
        retrieve_user_handler=retrieve_user_handler,
        token_secret="abc1234",
        exclude=["/"],
        type_encoders={CustomUser: lambda u: {"id": u.id}},
    )

    @get()
    def handler() -> Response[User]:
        data = CustomUser(id="1")
        return jwt_cookie_auth.login(identifier=str(data.id), response_body=data)

    with create_test_client([handler]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_201_CREATED


async def retrieve_user_handler(token: Token, connection: "ASGIConnection[Any, Any, Any, Any]") -> Any:
    return User(name="moishe", id=uuid4())


@pytest.mark.parametrize(
    "config",
    (
        JWTAuth[User](
            retrieve_user_handler=retrieve_user_handler,
            token_secret="abc1234",
            exclude=["/"],
        ),
        JWTCookieAuth[User](
            retrieve_user_handler=retrieve_user_handler,
            token_secret="abc1234",
            exclude=["/"],
        ),
        OAuth2PasswordBearerAuth(
            token_url="/", exclude=["/"], token_secret="abc123", retrieve_user_handler=retrieve_user_handler
        ),
    ),
)
def test_returns_token_in_response_when_configured(config: JWTAuth) -> None:
    @get()
    def handler() -> Response[User]:
        return config.login(identifier="123", send_token_as_response_body=True)

    with create_test_client([handler]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_201_CREATED
        assert isinstance(response.json(), dict) and response.json()


@pytest.mark.parametrize(
    "config",
    (
        JWTAuth[User](
            retrieve_user_handler=retrieve_user_handler,
            token_secret="abc1234",
            exclude=["/"],
        ),
        JWTCookieAuth[User](
            retrieve_user_handler=retrieve_user_handler,
            token_secret="abc1234",
            exclude=["/"],
        ),
        OAuth2PasswordBearerAuth(
            token_url="/", exclude=["/"], token_secret="abc123", retrieve_user_handler=retrieve_user_handler
        ),
    ),
)
def test_returns_none_when_response_body_is_none(config: JWTAuth) -> None:
    @get()
    def handler() -> Response[User]:
        return config.login(identifier="123", send_token_as_response_body=True, response_body=None)

    with create_test_client([handler]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_201_CREATED
        assert response.json() is None
