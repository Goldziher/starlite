from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, Union, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_lazy_fixtures import lf

from litestar import Controller, Litestar, Request, WebSocket
from litestar.datastructures import State
from litestar.di import Provide
from litestar.dto import DataclassDTO, dto_field
from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers.websocket_handlers import WebsocketListener, websocket_listener
from litestar.testing import create_test_client
from litestar.types.asgi_types import WebSocketMode


@pytest.fixture
def listener_class(mock: MagicMock) -> Type[WebsocketListener]:
    class Listener(WebsocketListener):
        def on_receive(self, data: str) -> str:  # pyright: ignore
            mock(data)
            return data

    return Listener


@pytest.fixture
def sync_listener_callable(mock: MagicMock) -> websocket_listener:
    def listener(data: str) -> str:
        mock(data)
        return data

    return websocket_listener("/")(listener)


@pytest.fixture
def async_listener_callable(mock: MagicMock) -> websocket_listener:
    async def listener(data: str) -> str:
        mock(data)
        return data

    return websocket_listener("/")(listener)


@pytest.mark.parametrize(
    "listener",
    [
        lf("sync_listener_callable"),
        lf("async_listener_callable"),
        lf("listener_class"),
    ],
)
def test_basic_listener(mock: MagicMock, listener: Union[websocket_listener, Type[WebsocketListener]]) -> None:
    client = create_test_client([listener])
    with client.websocket_connect("/") as ws:
        ws.send_text("foo")
        assert ws.receive_text() == "foo"
        ws.send_text("bar")
        assert ws.receive_text() == "bar"

    assert mock.call_count == 2
    mock.assert_any_call("foo")
    mock.assert_any_call("bar")


@pytest.mark.parametrize("receive_mode", ["text", "binary"])
def test_listener_receive_bytes(receive_mode: WebSocketMode, mock: MagicMock) -> None:
    @websocket_listener("/", receive_mode=receive_mode)
    def handler(data: bytes) -> None:
        mock(data)

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send("foo", mode=receive_mode)

    mock.assert_called_once_with(b"foo")


@pytest.mark.parametrize("receive_mode", ["text", "binary"])
def test_listener_receive_string(receive_mode: WebSocketMode, mock: MagicMock) -> None:
    @websocket_listener("/", receive_mode=receive_mode)
    def handler(data: str) -> None:
        mock(data)

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send("foo", mode=receive_mode)

    mock.assert_called_once_with("foo")


@pytest.mark.parametrize("receive_mode", ["text", "binary"])
def test_listener_receive_json(receive_mode: WebSocketMode, mock: MagicMock) -> None:
    @websocket_listener("/", receive_mode=receive_mode)
    def handler(data: List[str]) -> None:
        mock(data)

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send_json(["foo", "bar"], mode=receive_mode)

    mock.assert_called_once_with(["foo", "bar"])


@dataclass
class User:
    name: str
    hidden: str = field(default="super secret", metadata=dto_field("private"))


@pytest.mark.parametrize("receive_mode", ["text", "binary"])
def test_listener_receive_with_dto(receive_mode: WebSocketMode) -> None:
    user_dto = DataclassDTO[User]
    value: Any = None

    @websocket_listener("/", receive_mode=receive_mode, dto=user_dto, return_dto=None)
    def handler(data: User) -> None:
        nonlocal value
        value = data

    client = create_test_client([handler], openapi_config=None)
    with client.websocket_connect("/") as ws:
        ws.send_json({"name": "litestar user", "hidden": "whoops"}, mode=receive_mode)

    assert isinstance(value, User)
    assert value.name == "litestar user"
    assert value.hidden == "super secret"


@pytest.mark.parametrize("send_mode", ["text", "binary"])
def test_listener_return_bytes(send_mode: WebSocketMode) -> None:
    @websocket_listener("/", send_mode=send_mode)
    def handler(data: str) -> bytes:
        return data.encode("utf-8")

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send_text("foo")
        if send_mode == "text":
            assert ws.receive_text() == "foo"
        else:
            assert ws.receive_bytes() == b"foo"


@pytest.mark.parametrize("send_mode", ["text", "binary"])
def test_listener_send_json(send_mode: WebSocketMode) -> None:
    @websocket_listener("/", send_mode=send_mode)
    def handler(data: str) -> Dict[str, str]:
        return {"data": data}

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send_text("foo")
        assert ws.receive_json(mode=send_mode) == {"data": "foo"}


@pytest.mark.parametrize("send_mode", ["text", "binary"])
def test_listener_send_with_dto(send_mode: WebSocketMode, mock: MagicMock) -> None:
    @dataclass
    class User:
        name: str
        hidden: str = field(default="super secret", metadata=dto_field("private"))

    user_dto = DataclassDTO[User]

    @websocket_listener("/", send_mode=send_mode, dto=user_dto, signature_namespace={"User": User})
    def handler(data: User) -> User:
        return data

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send_json({"name": "litestar user"})
        assert ws.receive_json(mode=send_mode) == {"name": "litestar user"}


def test_listener_return_none() -> None:
    @websocket_listener("/")
    def handler(data: str) -> None:
        return data  # type: ignore[return-value]

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send_text("foo")


def test_listener_return_optional_none() -> None:
    @websocket_listener("/")
    def handler(data: str) -> Optional[str]:
        return "world" if data == "hello" else None

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send_text("hello")
        assert ws.receive_text() == "world"
        ws.send_text("goodbye")


def test_listener_pass_socket(mock: MagicMock) -> None:
    @websocket_listener("/")
    def handler(data: str, socket: WebSocket) -> Dict[str, str]:
        mock(socket=socket)
        return {"data": data}

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send_text("foo")
        assert ws.receive_json() == {"data": "foo"}

    assert isinstance(mock.call_args.kwargs["socket"], WebSocket)


def test_listener_pass_additional_dependencies(mock: MagicMock) -> None:
    async def foo_dependency(state: State) -> int:
        if not hasattr(state, "foo"):
            state.foo = 0
        state.foo += 1
        return cast("int", state.foo)

    @websocket_listener("/", dependencies={"foo": Provide(foo_dependency)})
    def handler(data: str, foo: int) -> Dict[str, Union[str, int]]:
        return {"data": data, "foo": foo}

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        ws.send_text("something")
        ws.send_text("something")
        assert ws.receive_json() == {"data": "something", "foo": 1}


def test_listener_callback_no_data_arg_raises() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @websocket_listener("/")
        def handler() -> None: ...

        handler.on_registration(Litestar())


def test_listener_callback_request_and_body_arg_raises() -> None:
    with pytest.raises(ImproperlyConfiguredException):

        @websocket_listener("/")
        def handler_request(data: str, request: Request) -> None: ...

        handler_request.on_registration(Litestar())

    with pytest.raises(ImproperlyConfiguredException):

        @websocket_listener("/")
        def handler_body(data: str, body: bytes) -> None: ...

        handler_body.on_registration(Litestar())


def test_listener_accept_connection_callback() -> None:
    async def accept_connection(socket: WebSocket) -> None:
        await socket.accept(headers={"Cookie": "custom-cookie"})

    @websocket_listener("/", connection_accept_handler=accept_connection)
    def handler(data: bytes) -> None:
        return None

    client = create_test_client([handler])
    with client.websocket_connect("/") as ws:
        assert ws.extra_headers == [(b"cookie", b"custom-cookie")]


def test_connection_callbacks() -> None:
    on_accept_mock = MagicMock()
    on_disconnect_mock = MagicMock()

    def on_accept(socket: WebSocket) -> None:
        on_accept_mock()

    def on_disconnect(socket: WebSocket) -> None:
        on_disconnect_mock()

    @websocket_listener("/", on_accept=on_accept, on_disconnect=on_disconnect)
    def handler(data: bytes) -> None:
        pass

    client = create_test_client([handler])
    with client.websocket_connect("/"):
        pass

    on_accept_mock.assert_called_once()
    on_disconnect_mock.assert_called_once()


def test_connection_lifespan() -> None:
    on_accept = MagicMock()
    on_disconnect = MagicMock()

    @asynccontextmanager
    async def lifespan(socket: WebSocket) -> AsyncGenerator[None, None]:
        on_accept(socket)
        try:
            yield
        finally:
            on_disconnect(socket)

    @websocket_listener("/", connection_lifespan=lifespan)
    def handler(data: bytes) -> None:
        pass

    client = create_test_client([handler])
    with client.websocket_connect("/", timeout=1):
        pass

    on_accept.assert_called_once()
    on_disconnect.assert_called_once()


def test_listener_in_controller() -> None:
    # test for https://github.com/litestar-org/litestar/issues/1615

    class ClientController(Controller):
        path: str = "/"

        @websocket_listener("/ws")
        async def websocket_handler(self, data: str, socket: WebSocket) -> str:
            return data

    with create_test_client(ClientController) as client, client.websocket_connect("/ws") as ws:
        ws.send_text("foo")
        data = ws.receive_text(timeout=1)
        assert data == "foo"


def test_lifespan_dependencies() -> None:
    mock = MagicMock()

    @asynccontextmanager
    async def lifespan(name: str, state: State, query: dict) -> AsyncGenerator[None, None]:
        mock(name=name, state=state, query=query)
        yield

    @websocket_listener("/{name:str}", connection_lifespan=lifespan)
    async def handler(data: str) -> None:
        pass

    with create_test_client([handler]) as client, client.websocket_connect("/foo") as ws:
        ws.send_text("")

    assert mock.call_args_list[0].kwargs["name"] == "foo"
    assert isinstance(mock.call_args_list[0].kwargs["state"], State)
    assert isinstance(mock.call_args_list[0].kwargs["query"], dict)


def test_hook_dependencies() -> None:
    on_accept_mock = MagicMock()
    on_disconnect_mock = MagicMock()

    def some_dependency() -> str:
        return "hello"

    def on_accept(name: str, state: State, query: dict, some: str) -> None:
        on_accept_mock(name=name, state=state, query=query, some=some)

    def on_disconnect(name: str, state: State, query: dict, some: str) -> None:
        on_disconnect_mock(name=name, state=state, query=query, some=some)

    @websocket_listener("/{name: str}", on_accept=on_accept, on_disconnect=on_disconnect)
    def handler(data: bytes) -> None:
        pass

    with create_test_client([handler], dependencies={"some": some_dependency}) as client, client.websocket_connect(
        "/foo"
    ) as ws:
        ws.send_text("")

    on_accept_kwargs = on_accept_mock.call_args_list[0].kwargs
    assert on_accept_kwargs["name"] == "foo"
    assert on_accept_kwargs["some"] == "hello"
    assert isinstance(on_accept_kwargs["state"], State)
    assert isinstance(on_accept_kwargs["query"], dict)

    on_disconnect_kwargs = on_disconnect_mock.call_args_list[0].kwargs
    assert on_disconnect_kwargs["name"] == "foo"
    assert on_disconnect_kwargs["some"] == "hello"
    assert isinstance(on_disconnect_kwargs["state"], State)
    assert isinstance(on_disconnect_kwargs["query"], dict)


def test_websocket_listener_class_hook_dependencies() -> None:
    on_accept_mock = MagicMock()
    on_disconnect_mock = MagicMock()

    def some_dependency() -> str:
        return "hello"

    class Listener(WebsocketListener):
        path = "/{name: str}"

        def on_accept(self, name: str, state: State, query: dict, some: str) -> None:  # type: ignore[override]
            on_accept_mock(name=name, state=state, query=query, some=some)

        def on_disconnect(self, name: str, state: State, query: dict, some: str) -> None:  # type: ignore[override]
            on_disconnect_mock(name=name, state=state, query=query, some=some)

        def on_receive(self, data: bytes) -> None:  # pyright: ignore
            pass

    with create_test_client([Listener], dependencies={"some": some_dependency}) as client, client.websocket_connect(
        "/foo"
    ) as ws:
        ws.send_text("")

    on_accept_kwargs = on_accept_mock.call_args_list[0].kwargs
    assert on_accept_kwargs["name"] == "foo"
    assert on_accept_kwargs["some"] == "hello"
    assert isinstance(on_accept_kwargs["state"], State)
    assert isinstance(on_accept_kwargs["query"], dict)

    on_disconnect_kwargs = on_disconnect_mock.call_args_list[0].kwargs
    assert on_disconnect_kwargs["name"] == "foo"
    assert on_disconnect_kwargs["some"] == "hello"
    assert isinstance(on_disconnect_kwargs["state"], State)
    assert isinstance(on_disconnect_kwargs["query"], dict)


@pytest.mark.parametrize("hook_name", ["on_accept", "on_disconnect", "connection_accept_handler"])
def test_listeners_lifespan_hooks_and_manager_raises(hook_name: str) -> None:
    @asynccontextmanager
    async def lifespan() -> AsyncGenerator[None, None]:
        yield

    hook_callback = AsyncMock()

    with pytest.raises(ImproperlyConfiguredException):

        @websocket_listener("/", **{hook_name: hook_callback}, connection_lifespan=lifespan)  # pyright: ignore
        def handler(data: bytes) -> None:
            pass
