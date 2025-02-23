from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest

from litestar import Litestar, get, websocket
from litestar.connection import Request, WebSocket
from litestar.enums import HttpMethod
from litestar.exceptions import PermissionDeniedException, WebSocketDisconnect
from litestar.middleware.authentication import (
    AbstractAuthenticationMiddleware,
    AuthenticationResult,
)
from litestar.middleware.base import DefineMiddleware
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection


async def dummy_app(scope: Any, receive: Any, send: Any) -> None:
    return None


@dataclass
class User:
    name: str
    id: int


@dataclass
class Auth:
    props: str


user = User(name="moishe", id=100)
auth = Auth(props="abc")

state: dict[str, AuthenticationResult] = {}


class AuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: "ASGIConnection") -> AuthenticationResult:
        param = connection.headers.get("Authorization")
        if param in state:
            return state.pop(param)
        raise PermissionDeniedException("unauthenticated")


def test_authentication_middleware_http_routes() -> None:
    @get(path="/")
    def http_route_handler(request: Request[User, Auth, Any]) -> None:
        assert isinstance(request.user, User)
        assert isinstance(request.auth, Auth)

    client = create_test_client(route_handlers=[http_route_handler], middleware=[AuthMiddleware])
    token = "abc"
    error_response = client.get("/", headers={"Authorization": token})
    assert error_response.status_code == HTTP_403_FORBIDDEN
    state[token] = AuthenticationResult(user=user, auth=auth)
    success_response = client.get("/", headers={"Authorization": token})
    assert success_response.status_code == HTTP_200_OK


def test_authentication_middleware_not_installed_raises_for_user_scope_http() -> None:
    @get(path="/")
    def http_route_handler_user_scope(request: Request[User, None, Any]) -> None:
        assert request.user

    client = create_test_client(route_handlers=[http_route_handler_user_scope])
    error_response = client.get("/", headers={"Authorization": "nope"})
    assert error_response.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_authentication_middleware_not_installed_raises_for_auth_scope_http() -> None:
    @get(path="/")
    def http_route_handler_auth_scope(request: Request[None, Auth, Any]) -> None:
        assert request.auth

    client = create_test_client(route_handlers=[http_route_handler_auth_scope])
    error_response = client.get("/", headers={"Authorization": "nope"})
    assert error_response.status_code == HTTP_500_INTERNAL_SERVER_ERROR


@websocket(path="/")
async def websocket_route_handler(socket: WebSocket[User, Auth, Any]) -> None:
    await socket.accept()
    assert isinstance(socket.user, User)
    assert isinstance(socket.auth, Auth)
    assert isinstance(socket.app, Litestar)
    await socket.send_json({"data": "123"})
    await socket.close()


def test_authentication_middleware_websocket_routes() -> None:
    token = "abc"
    client = create_test_client(route_handlers=websocket_route_handler, middleware=[AuthMiddleware])
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/", headers={"Authorization": token}) as ws:
        assert ws.receive_json()
    state[token] = AuthenticationResult(user=user, auth=auth)
    with client.websocket_connect("/", headers={"Authorization": token}) as ws:
        assert ws.receive_json()


def test_authentication_middleware_not_installed_raises_for_user_scope_websocket() -> None:
    @websocket(path="/")
    async def route_handler(socket: WebSocket[User, Auth, Any]) -> None:
        await socket.accept()
        assert isinstance(socket.user, User)

    client = create_test_client(route_handlers=route_handler)
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/", headers={"Authorization": "yep"}) as ws:
        ws.receive_json()


def test_authentication_middleware_not_installed_raises_for_auth_scope_websocket() -> None:
    @websocket(path="/")
    async def route_handler(socket: WebSocket[User, Auth, Any]) -> None:
        await socket.accept()
        assert isinstance(socket.auth, Auth)

    client = create_test_client(route_handlers=route_handler)
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/", headers={"Authorization": "yep"}) as ws:
        ws.receive_json()


def test_authentication_middleware_exclude() -> None:
    auth_mw = DefineMiddleware(AuthMiddleware, exclude=["north", "south"])

    @get("/north/{value:int}")
    def north_handler(value: int) -> dict[str, int]:
        return {"value": value}

    @get("/south")
    def south_handler() -> None:
        return None

    @get("/west")
    def west_handler() -> None:
        return None

    with create_test_client(
        route_handlers=[north_handler, south_handler, west_handler],
        middleware=[auth_mw],
    ) as client:
        response = client.get("/north/1")
        assert response.status_code == HTTP_200_OK

        response = client.get("/south")
        assert response.status_code == HTTP_200_OK

        response = client.get("/west")
        assert response.status_code == HTTP_403_FORBIDDEN


def test_authentication_middleware_exclude_from_auth() -> None:
    auth_mw = DefineMiddleware(AuthMiddleware, exclude=["south", "east"])

    @get("/north/{value:int}", exclude_from_auth=True)
    def north_handler(value: int) -> dict[str, int]:
        return {"value": value}

    @get("/south")
    def south_handler() -> None:
        return None

    @get("/west")
    def west_handler() -> None:
        return None

    @get("/east", exclude_from_auth=True)
    def east_handler() -> None:
        return None

    with create_test_client(
        route_handlers=[north_handler, south_handler, west_handler, east_handler],
        middleware=[auth_mw],
    ) as client:
        response = client.get("/north/1")
        assert response.status_code == HTTP_200_OK

        response = client.get("/south")
        assert response.status_code == HTTP_200_OK

        response = client.get("/east")
        assert response.status_code == HTTP_200_OK

        response = client.get("/west")
        assert response.status_code == HTTP_403_FORBIDDEN


def test_authentication_middleware_exclude_from_auth_custom_key() -> None:
    auth_mw = DefineMiddleware(AuthMiddleware, exclude=["south", "east"], exclude_from_auth_key="my_exclude_key")

    @get("/north/{value:int}", my_exclude_key=True)
    def north_handler(value: int) -> dict[str, int]:
        return {"value": value}

    @get("/south")
    def south_handler() -> None:
        return None

    @get("/west")
    def west_handler() -> None:
        return None

    @get("/east", my_exclude_key=True)
    def east_handler() -> None:
        return None

    with create_test_client(
        route_handlers=[north_handler, south_handler, west_handler, east_handler],
        middleware=[auth_mw],
    ) as client:
        response = client.get("/north/1")
        assert response.status_code == HTTP_200_OK

        response = client.get("/south")
        assert response.status_code == HTTP_200_OK

        response = client.get("/east")
        assert response.status_code == HTTP_200_OK

        response = client.get("/west")
        assert response.status_code == HTTP_403_FORBIDDEN


def test_authentication_exclude_http_methods() -> None:
    auth_mw = DefineMiddleware(AuthMiddleware, exclude_http_methods=[HttpMethod.GET])

    @get("/")
    def exclude_get_handler() -> None:
        return None

    with create_test_client(route_handlers=[exclude_get_handler], middleware=[auth_mw]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

        response = client.options("/")
        assert response.status_code == HTTP_403_FORBIDDEN


def test_authentication_exclude_http_methods_default() -> None:
    auth_mw = DefineMiddleware(AuthMiddleware)

    @get("/")
    def exclude_get_handler() -> None:
        return None

    with create_test_client(route_handlers=[exclude_get_handler], middleware=[auth_mw]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_403_FORBIDDEN

        # OPTIONS should be excluded by default
        response = client.options("/")
        assert response.is_success
