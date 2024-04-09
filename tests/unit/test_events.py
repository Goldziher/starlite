from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_lazy_fixtures import lf

from litestar import Litestar, Request, get
from litestar.events.emitter import SimpleEventEmitter
from litestar.events.listener import EventListener, listener
from litestar.exceptions import ImproperlyConfiguredException
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client
from litestar.types import AnyIOBackend


@pytest.fixture()
def mock() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def sync_listener(mock: MagicMock) -> EventListener:
    @listener("test_event")
    def listener_fn(*args: Any, **kwargs: Any) -> None:
        mock(*args, **kwargs)

    return listener_fn


@pytest.fixture()
def async_listener(mock: MagicMock) -> EventListener:
    @listener("test_event")
    async def listener_fn(*args: Any, **kwargs: Any) -> None:
        mock(*args, **kwargs)

    return listener_fn


@pytest.mark.parametrize("event_listener", [lf("sync_listener"), lf("async_listener")])
def test_event_listener(mock: MagicMock, event_listener: EventListener, anyio_backend: AnyIOBackend) -> None:
    @get("/")
    def route_handler(request: Request[Any, Any, Any]) -> None:
        request.app.emit("test_event", "positional", keyword="keyword-value")

    with create_test_client(
        route_handlers=[route_handler], listeners=[event_listener], backend=anyio_backend
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

    mock.assert_called_with("positional", keyword="keyword-value")


async def test_shutdown_awaits_pending(async_listener: EventListener, mock: MagicMock) -> None:
    async with SimpleEventEmitter([async_listener]) as emitter:
        for _ in range(100):
            emitter.emit("test_event")

    assert mock.call_count == 100


def test_multiple_event_listeners(
    async_listener: EventListener, sync_listener: EventListener, mock: MagicMock, anyio_backend: AnyIOBackend
) -> None:
    @get("/")
    def route_handler(request: Request[Any, Any, Any]) -> None:
        request.app.emit("test_event")

    with create_test_client(
        route_handlers=[route_handler], listeners=[async_listener, sync_listener], backend=anyio_backend
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

    assert mock.call_count == 2


def test_multiple_event_ids(mock: MagicMock, anyio_backend: AnyIOBackend) -> None:
    @listener("test_event_1", "test_event_2")
    def event_handler() -> None:
        mock()

    @get("/{event_id:int}")
    def route_handler(request: Request[Any, Any, Any], event_id: int) -> None:
        request.app.emit(f"test_event_{event_id}")

    with create_test_client(route_handlers=[route_handler], listeners=[event_handler], backend=anyio_backend) as client:
        response_1 = client.get("/1")
        response_2 = client.get("/2")
        assert response_1.status_code == HTTP_200_OK
        assert response_2.status_code == HTTP_200_OK

    assert mock.call_count == 2


async def test_raises_when_decorator_called_without_callable() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        listener("test_even")(True)  # type: ignore[arg-type]


async def test_raises_when_not_initialized() -> None:
    app = Litestar([])

    with pytest.raises(RuntimeError):
        app.emit("x")


async def test_raises_when_not_listener_are_registered_for_an_event_id(async_listener: EventListener) -> None:
    with create_test_client(route_handlers=[], listeners=[async_listener]) as client:
        with pytest.raises(ImproperlyConfiguredException):
            client.app.emit("x")


async def test_event_listener_raises_exception(async_listener: EventListener, mock: MagicMock) -> None:
    """Test that an event listener that raises an exception does not prevent other listeners from being called.

    https://github.com/litestar-org/litestar/issues/2809
    """

    error_mock = MagicMock()

    @listener("error_event")
    async def raising_listener(*args: Any, **kwargs: Any) -> None:
        error_mock()
        raise ValueError("test")

    @get("/error")
    def route_handler_1(request: Request[Any, Any, Any]) -> None:
        request.app.emit("error_event")

    @get("/no-error")
    def route_handler_2(request: Request[Any, Any, Any]) -> None:
        request.app.emit("test_event")

    with create_test_client(
        route_handlers=[route_handler_1, route_handler_2], listeners=[async_listener, raising_listener]
    ) as client:
        first_response = client.get("/error")
        second_response = client.get("/no-error")
        assert first_response.status_code == HTTP_200_OK
        assert second_response.status_code == HTTP_200_OK

    error_mock.assert_called()
    mock.assert_called()
