from queue import Empty
from typing import TYPE_CHECKING, Callable, Dict, NoReturn, Optional, Union, cast

from _pytest.fixtures import FixtureRequest

from litestar import Controller, WebSocket, delete, head, patch, put, websocket
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.testing import AsyncTestClient, WebSocketTestSession, create_async_test_client, create_test_client

if TYPE_CHECKING:
    from litestar.middleware.session.base import BaseBackendConfig
    from litestar.types import (
        AnyIOBackend,
        HTTPResponseBodyEvent,
        HTTPResponseStartEvent,
        Receive,
        Scope,
        Send,
    )

from typing import Any, Type

import pytest

from litestar import Litestar, Request, get, post
from litestar.stores.base import Store
from litestar.testing import TestClient
from litestar.utils.helpers import get_exception_group
from tests.helpers import maybe_async, maybe_async_cm

_ExceptionGroup = get_exception_group()

AnyTestClient = Union[TestClient, AsyncTestClient]


async def mock_asgi_app(scope: "Scope", receive: "Receive", send: "Send") -> None:
    pass


@pytest.fixture(params=[AsyncTestClient, TestClient])
def test_client_cls(request: FixtureRequest) -> Type[AnyTestClient]:
    return cast(Type[AnyTestClient], request.param)


@pytest.mark.parametrize("with_domain", [False, True])
async def test_test_client_set_session_data(
    with_domain: bool,
    session_backend_config: "BaseBackendConfig",
    test_client_backend: "AnyIOBackend",
    test_client_cls: Type[AnyTestClient],
) -> None:
    session_data = {"foo": "bar"}

    if with_domain:
        session_backend_config.domain = "testserver.local"

    @get(path="/test")
    def get_session_data(request: Request) -> Dict[str, Any]:
        return request.session

    app = Litestar(route_handlers=[get_session_data], middleware=[session_backend_config.middleware])

    async with maybe_async_cm(
        test_client_cls(app=app, session_config=session_backend_config, backend=test_client_backend)  # pyright: ignore
    ) as client:
        await maybe_async(client.set_session_data(session_data))  # type: ignore[attr-defined]
        assert session_data == (await maybe_async(client.get("/test"))).json()  # type: ignore[attr-defined]


@pytest.mark.parametrize("with_domain", [False, True])
async def test_test_client_get_session_data(
    with_domain: bool,
    session_backend_config: "BaseBackendConfig",
    test_client_backend: "AnyIOBackend",
    store: Store,
    test_client_cls: Type[AnyTestClient],
) -> None:
    session_data = {"foo": "bar"}

    if with_domain:
        session_backend_config.domain = "testserver.local"

    @post(path="/test")
    def set_session_data(request: Request) -> None:
        request.session.update(session_data)

    app = Litestar(
        route_handlers=[set_session_data], middleware=[session_backend_config.middleware], stores={"session": store}
    )

    async with maybe_async_cm(
        test_client_cls(app=app, session_config=session_backend_config, backend=test_client_backend)  # pyright: ignore
    ) as client:
        await maybe_async(client.post("/test"))  # type: ignore[attr-defined]
        assert await maybe_async(client.get_session_data()) == session_data  # type: ignore[attr-defined]


async def test_use_testclient_in_endpoint(
    test_client_backend: "AnyIOBackend", test_client_cls: Type[AnyTestClient]
) -> None:
    """this test is taken from starlette."""

    @get("/")
    def mock_service_endpoint() -> dict:
        return {"mock": "example"}

    mock_service = Litestar(route_handlers=[mock_service_endpoint])

    @get("/")
    async def homepage() -> Any:
        local_client = test_client_cls(mock_service, backend=test_client_backend)
        local_response = await maybe_async(local_client.get("/"))
        return local_response.json()  # type: ignore[union-attr]

    app = Litestar(route_handlers=[homepage])

    client = test_client_cls(app)
    response = await maybe_async(client.get("/"))
    assert response.json() == {"mock": "example"}  # type: ignore[union-attr]


def raise_error(app: Litestar) -> NoReturn:
    raise RuntimeError()


async def test_error_handling_on_startup(
    test_client_backend: "AnyIOBackend", test_client_cls: Type[AnyTestClient]
) -> None:
    with pytest.raises(_ExceptionGroup):
        async with maybe_async_cm(
            test_client_cls(Litestar(on_startup=[raise_error]), backend=test_client_backend)  # pyright: ignore
        ):
            pass


async def test_error_handling_on_shutdown(
    test_client_backend: "AnyIOBackend", test_client_cls: Type[AnyTestClient]
) -> None:
    with pytest.raises(RuntimeError):
        async with maybe_async_cm(
            test_client_cls(Litestar(on_shutdown=[raise_error]), backend=test_client_backend)  # pyright: ignore
        ):
            pass


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete", "head", "options"])
async def test_client_interface(
    method: str, test_client_backend: "AnyIOBackend", test_client_cls: Type[AnyTestClient]
) -> None:
    async def asgi_app(scope: "Scope", receive: "Receive", send: "Send") -> None:
        start_event: HTTPResponseStartEvent = {
            "type": "http.response.start",
            "status": HTTP_200_OK,
            "headers": [(b"content-type", b"text/plain")],
        }
        await send(start_event)
        body_event: HTTPResponseBodyEvent = {"type": "http.response.body", "body": b"", "more_body": False}
        await send(body_event)

    client = test_client_cls(asgi_app, backend=test_client_backend)
    if method == "get":
        response = await maybe_async(client.get("/"))
    elif method == "post":
        response = await maybe_async(client.post("/"))
    elif method == "put":
        response = await maybe_async(client.put("/"))
    elif method == "patch":
        response = await maybe_async(client.patch("/"))
    elif method == "delete":
        response = await maybe_async(client.delete("/"))
    elif method == "head":
        response = await maybe_async(client.head("/"))
    else:
        response = await maybe_async(client.options("/"))
    assert response.status_code == HTTP_200_OK  # type: ignore[union-attr]


def test_warns_problematic_domain(test_client_cls: Type[AnyTestClient]) -> None:
    with pytest.warns(UserWarning):
        test_client_cls(app=mock_asgi_app, base_url="http://testserver")


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete", "head", "options"])
async def test_client_interface_context_manager(
    method: str, test_client_backend: "AnyIOBackend", test_client_cls: Type[AnyTestClient]
) -> None:
    class MockController(Controller):
        @get("/")
        def mock_service_endpoint_get(self) -> dict:
            return {"mock": "example"}

        @post("/")
        def mock_service_endpoint_post(self) -> dict:
            return {"mock": "example"}

        @put("/")
        def mock_service_endpoint_put(self) -> None: ...

        @patch("/")
        def mock_service_endpoint_patch(self) -> None: ...

        @delete("/")
        def mock_service_endpoint_delete(self) -> None: ...

        @head("/")
        def mock_service_endpoint_head(self) -> None: ...

    mock_service = Litestar(route_handlers=[MockController])
    async with maybe_async_cm(test_client_cls(mock_service, backend=test_client_backend)) as client:  # pyright: ignore
        if method == "get":
            response = await maybe_async(client.get("/"))  # type: ignore[attr-defined]
            assert response.status_code == HTTP_200_OK  # pyright: ignore
        elif method == "post":
            response = await maybe_async(client.post("/"))  # type: ignore[attr-defined]
            assert response.status_code == HTTP_201_CREATED  # pyright: ignore
        elif method == "put":
            response = await maybe_async(client.put("/"))  # type: ignore[attr-defined]
            assert response.status_code == HTTP_200_OK  # pyright: ignore
        elif method == "patch":
            response = await maybe_async(client.patch("/"))  # type: ignore[attr-defined]
            assert response.status_code == HTTP_200_OK  # pyright: ignore
        elif method == "delete":
            response = await maybe_async(client.delete("/"))  # type: ignore[attr-defined]
            assert response.status_code == HTTP_204_NO_CONTENT  # pyright: ignore
        elif method == "head":
            response = await maybe_async(client.head("/"))  # type: ignore[attr-defined]
            assert response.status_code == HTTP_200_OK  # pyright: ignore
        else:
            response = await maybe_async(client.options("/"))  # type: ignore[attr-defined]
            assert response.status_code == HTTP_204_NO_CONTENT  # pyright: ignore


@pytest.mark.parametrize("block,timeout", [(False, None), (False, 0.001), (True, 0.001)])
@pytest.mark.parametrize(
    "receive_method",
    [
        WebSocketTestSession.receive,
        WebSocketTestSession.receive_json,
        WebSocketTestSession.receive_text,
        WebSocketTestSession.receive_bytes,
    ],
)
def test_websocket_test_session_block_timeout(
    receive_method: Callable[..., Any], block: bool, timeout: Optional[float], anyio_backend: "AnyIOBackend"
) -> None:
    @websocket()
    async def handler(socket: WebSocket) -> None:
        await socket.accept()

    with pytest.raises(Empty):
        with create_test_client(handler, backend=anyio_backend) as client, client.websocket_connect("/") as ws:
            receive_method(ws, timeout=timeout, block=block)


def test_websocket_accept_timeout(anyio_backend: "AnyIOBackend") -> None:
    @websocket()
    async def handler(socket: WebSocket) -> None:
        pass

    with create_test_client(handler, backend=anyio_backend, timeout=0.1) as client, pytest.raises(
        Empty
    ), client.websocket_connect("/"):
        pass


@pytest.mark.parametrize("block,timeout", [(False, None), (False, 0.001), (True, 0.001)])
@pytest.mark.parametrize(
    "receive_method",
    [
        WebSocketTestSession.receive,
        WebSocketTestSession.receive_json,
        WebSocketTestSession.receive_text,
        WebSocketTestSession.receive_bytes,
    ],
)
async def test_websocket_test_session_block_timeout_async(
    receive_method: Callable[..., Any], block: bool, timeout: Optional[float], anyio_backend: "AnyIOBackend"
) -> None:
    @websocket()
    async def handler(socket: WebSocket) -> None:
        await socket.accept()

    with pytest.raises(Empty):
        async with create_async_test_client(handler, backend=anyio_backend) as client:
            with await client.websocket_connect("/") as ws:
                receive_method(ws, timeout=timeout, block=block)


async def test_websocket_accept_timeout_async(anyio_backend: "AnyIOBackend") -> None:
    @websocket()
    async def handler(socket: WebSocket) -> None:
        pass

    async with create_async_test_client(handler, backend=anyio_backend, timeout=0.1) as client:
        with pytest.raises(Empty):
            with await client.websocket_connect("/"):
                pass


async def test_websocket_connect_async(anyio_backend: "AnyIOBackend") -> None:
    @websocket()
    async def handler(socket: WebSocket) -> None:
        await socket.accept()
        data = await socket.receive_json()
        await socket.send_json(data)
        await socket.close()

    async with create_async_test_client(handler, backend=anyio_backend, timeout=0.1) as client:
        with await client.websocket_connect("/", subprotocols="wamp") as ws:
            ws.send_json({"data": "123"})
            data = ws.receive_json()
            assert data == {"data": "123"}
