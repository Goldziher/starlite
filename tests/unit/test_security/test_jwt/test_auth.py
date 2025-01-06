import dataclasses
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

import jwt
import msgspec
import pytest
from hypothesis import given, settings
from hypothesis.strategies import dictionaries, integers, none, one_of, sampled_from, text, timedeltas
from typing_extensions import TypeAlias

from litestar import Litestar, Request, Response, get
from litestar.security.jwt import JWTAuth, JWTCookieAuth, OAuth2PasswordBearerAuth, Token
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.stores.memory import MemoryStore
from litestar.testing import TestClient, create_test_client
from tests.models import User, UserFactory

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection

pytestmark = pytest.mark.anyio


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


@pytest.mark.parametrize("auth_cls", [JWTAuth, JWTCookieAuth, OAuth2PasswordBearerAuth])
async def test_jwt_auth_custom_token_cls(auth_cls: Any) -> None:
    @dataclasses.dataclass
    class CustomToken(Token):
        random_field: int = 1

    async def retrieve_user_handler(token: CustomToken, _: "ASGIConnection") -> Any:
        return object()

    token_secret = secrets.token_hex()

    if auth_cls is OAuth2PasswordBearerAuth:
        jwt_auth = auth_cls(
            token_secret=token_secret,
            retrieve_user_handler=retrieve_user_handler,
            token_cls=CustomToken,
            token_url="http://testserver.local",
        )
    else:
        jwt_auth = auth_cls[Any](
            token_secret=token_secret,
            retrieve_user_handler=retrieve_user_handler,
            token_cls=CustomToken,
        )

    @get("/", middleware=[jwt_auth.middleware])
    def handler(request: Request[Any, CustomToken, Any]) -> Dict[str, Any]:
        return {
            "is_token_cls": isinstance(request.auth, CustomToken),
            "token": dataclasses.asdict(request.auth),
        }

    header = jwt_auth.format_auth_header(
        jwt_auth.create_token(
            "foo",
            token_extras={"foo": "bar"},
            # pass a string here as value to ensure things get converted properly
            random_field="2",
        ),
    )

    with create_test_client(route_handlers=[handler]) as client:
        response = client.get("/", headers={"Authorization": header})
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["is_token_cls"] is True
        assert response_data["token"]["extras"] == {"foo": "bar"}
        assert response_data["token"]["random_field"] == 2


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


async def test_jwt_auth_validation_error_returns_not_authorized() -> None:
    # if the value of a field has an invalid type, msgspec will raise a 'ValidationError'.
    # this should still result in a '401' status response
    async def retrieve_user_handler(token: Token, _: "ASGIConnection") -> Any:
        return object()

    token_secret = secrets.token_hex()

    jwt_auth = JWTAuth[Any](
        token_secret=token_secret,
        retrieve_user_handler=retrieve_user_handler,
    )

    @get("/", middleware=[jwt_auth.middleware])
    def handler() -> None:
        return None

    header = jwt_auth.format_auth_header(
        jwt.encode(
            {
                "sub": "foo",
                "exp": (datetime.now() + timedelta(days=1)).timestamp(),
                "iat": datetime.now().timestamp(),
                "iss": {"foo": "bar"},
            },
            key=token_secret,
        ),
    )

    with create_test_client(route_handlers=[handler]) as client:
        response = client.get("/", headers={"Authorization": header})
        assert response.status_code == 401


@pytest.mark.parametrize(
    "accepted_issuers, signing_issuer, expected_status_code",
    [
        (["issuer_a"], "issuer_a", 200),
        (["issuer_a", "issuer_b"], "issuer_a", 200),
        (["issuer_a", "issuer_b"], "issuer_b", 200),
        (["issuer_b"], "issuer_a", 401),
    ],
)
@pytest.mark.parametrize("auth_cls", [JWTAuth, JWTCookieAuth, OAuth2PasswordBearerAuth])
async def test_jwt_auth_verify_issuer(
    auth_cls: Any,
    accepted_issuers: List[str],
    signing_issuer: str,
    expected_status_code: int,
) -> None:
    async def retrieve_user_handler(token: Token, _: "ASGIConnection") -> Any:
        return object()

    token_secret = secrets.token_hex()

    if auth_cls is OAuth2PasswordBearerAuth:
        jwt_auth = auth_cls(
            token_secret=token_secret,
            retrieve_user_handler=retrieve_user_handler,
            token_url="http://testserver.local",
            accepted_issuers=accepted_issuers,
        )
    else:
        jwt_auth = auth_cls[Any](
            token_secret=token_secret,
            retrieve_user_handler=retrieve_user_handler,
            accepted_issuers=accepted_issuers,
        )

    @get("/", middleware=[jwt_auth.middleware])
    def handler() -> None:
        return None

    header = jwt_auth.format_auth_header(
        jwt_auth.create_token(
            identifier="foo",
            token_issuer=signing_issuer,
        ),
    )

    with create_test_client(route_handlers=[handler]) as client:
        response = client.get("/", headers={"Authorization": header})
        assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "accepted_audiences, token_audience, expected_status_code",
    [
        (["audience_a"], "audience_a", 200),
        (["audience_a", "audience_b"], "audience_a", 200),
        (["audience_a", "audience_b"], "audience_b", 200),
        (["audience_b"], "audience_a", 401),
    ],
)
@pytest.mark.parametrize("auth_cls", [JWTAuth, JWTCookieAuth, OAuth2PasswordBearerAuth])
async def test_jwt_auth_verify_audience(
    auth_cls: Any,
    accepted_audiences: List[str],
    token_audience: str,
    expected_status_code: int,
) -> None:
    async def retrieve_user_handler(token: Token, _: "ASGIConnection") -> Any:
        return object()

    token_secret = secrets.token_hex()

    if auth_cls is OAuth2PasswordBearerAuth:
        jwt_auth = auth_cls(
            token_secret=token_secret,
            retrieve_user_handler=retrieve_user_handler,
            token_url="http://testserver.local",
            accepted_audiences=accepted_audiences,
        )
    else:
        jwt_auth = auth_cls[Any](
            token_secret=token_secret,
            retrieve_user_handler=retrieve_user_handler,
            accepted_audiences=accepted_audiences,
        )

    @get("/", middleware=[jwt_auth.middleware])
    def handler() -> None:
        return None

    header = jwt_auth.format_auth_header(
        jwt_auth.create_token(
            identifier="foo",
            token_audience=token_audience,
        ),
    )

    with create_test_client(route_handlers=[handler]) as client:
        response = client.get("/", headers={"Authorization": header})
        assert response.status_code == expected_status_code


CreateJWTApp: TypeAlias = Callable[..., Tuple[JWTAuth, TestClient]]


@pytest.fixture()
def create_jwt_app(auth_cls: Any, request: pytest.FixtureRequest) -> CreateJWTApp:
    def create(**kwargs: Any) -> Tuple[JWTAuth, TestClient]:
        async def retrieve_user_handler(token: Token, _: "ASGIConnection") -> Any:
            return object()

        if auth_cls is OAuth2PasswordBearerAuth:
            jwt_auth = auth_cls(
                token_secret=secrets.token_hex(),
                retrieve_user_handler=retrieve_user_handler,
                token_url="http://testserver.local",
                **kwargs,
            )
        else:
            jwt_auth = auth_cls[Any](
                token_secret=secrets.token_hex(), retrieve_user_handler=retrieve_user_handler, **kwargs
            )

        @get("/", middleware=[jwt_auth.middleware])
        def handler() -> None:
            return None

        client = create_test_client(route_handlers=[handler]).__enter__()
        request.addfinalizer(client.__exit__)

        return jwt_auth, client

    return create


@pytest.fixture(params=[JWTAuth, JWTCookieAuth, OAuth2PasswordBearerAuth])
def auth_cls(request: pytest.FixtureRequest) -> Any:
    return request.param


@pytest.mark.parametrize(
    "accepted_audiences, token_audience, expected_status_code",
    [
        (["audience_a"], "audience_a", 200),
        ("audience_a", "audience_a", 200),
        (["audience_a"], ["audience_a", "audience_b"], 401),
        (["audience_b"], "audience_a", 401),
    ],
)
async def test_jwt_auth_strict_audience(
    accepted_audiences: List[str],
    token_audience: str,
    expected_status_code: int,
    create_jwt_app: CreateJWTApp,
) -> None:
    jwt_auth, client = create_jwt_app(strict_audience=True, accepted_audiences=accepted_audiences)

    header = jwt_auth.format_auth_header(
        jwt_auth.create_token(
            identifier="foo",
            token_audience=token_audience,
        ),
    )

    response = client.get("/", headers={"Authorization": header})
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "require_claims, token_claims, expected_status_code",
    [
        (["aud"], {"token_audience": "foo"}, 200),
        (["aud"], {}, 401),
        ([], {}, 200),
    ],
)
async def test_jwt_auth_require_claims(
    require_claims: List[str],
    token_claims: Dict[str, str],
    expected_status_code: int,
    create_jwt_app: CreateJWTApp,
) -> None:
    jwt_auth, client = create_jwt_app(require_claims=require_claims)

    header = jwt_auth.format_auth_header(
        jwt_auth.create_token(
            identifier="foo",
            **token_claims,  # type: ignore[arg-type]
        ),
    )

    response = client.get("/", headers={"Authorization": header})
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "token_expiration, verify_expiry, expected_status_code",
    [
        pytest.param((datetime.now(tz=timezone.utc) + timedelta(days=1)).timestamp(), True, 200, id="valid-verify"),
        pytest.param((datetime.now(tz=timezone.utc) + timedelta(days=1)).timestamp(), False, 200, id="valid-no_verify"),
        pytest.param(
            (datetime.now(tz=timezone.utc) - timedelta(days=1)).timestamp(), False, 200, id="invalid-no_verify"
        ),
        pytest.param((datetime.now(tz=timezone.utc) - timedelta(days=1)).timestamp(), True, 401, id="invalid-verify"),
    ],
)
async def test_jwt_auth_verify_exp(
    token_expiration: datetime,
    verify_expiry: bool,
    expected_status_code: int,
    create_jwt_app: CreateJWTApp,
) -> None:
    @dataclasses.dataclass
    class CustomToken(Token):
        def __post_init__(self) -> None:
            pass

    jwt_auth, client = create_jwt_app(verify_expiry=verify_expiry, token_cls=CustomToken)

    header = jwt_auth.format_auth_header(
        CustomToken(
            sub="foo",
            exp=token_expiration,
        ).encode(jwt_auth.token_secret, jwt_auth.algorithm),
    )

    response = client.get("/", headers={"Authorization": header})
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "token_nbf, verify_not_before, expected_status_code",
    [
        pytest.param((datetime.now(tz=timezone.utc) - timedelta(days=1)).timestamp(), True, 200, id="valid-verify"),
        pytest.param((datetime.now(tz=timezone.utc) - timedelta(days=1)).timestamp(), False, 200, id="valid-no_verify"),
        pytest.param(
            (datetime.now(tz=timezone.utc) + timedelta(days=1)).timestamp(), False, 200, id="invalid-no_verify"
        ),
        pytest.param((datetime.now(tz=timezone.utc) + timedelta(days=1)).timestamp(), True, 401, id="invalid-verify"),
    ],
)
async def test_jwt_auth_verify_nbf(
    token_nbf: datetime,
    verify_not_before: bool,
    expected_status_code: int,
    create_jwt_app: CreateJWTApp,
) -> None:
    @dataclasses.dataclass()
    class CustomToken(Token):
        nbf: Optional[float] = None

    jwt_auth, client = create_jwt_app(verify_not_before=verify_not_before, token_cls=CustomToken)

    header = jwt_auth.format_auth_header(jwt_auth.create_token("foo", nbf=token_nbf))

    response = client.get("/", headers={"Authorization": header})
    assert response.status_code == expected_status_code
