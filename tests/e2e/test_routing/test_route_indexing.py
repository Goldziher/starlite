from typing import TYPE_CHECKING, Any, Type

import pytest

from litestar import (
    Controller,
    Litestar,
    Router,
    asgi,
    delete,
    get,
    patch,
    post,
    put,
    websocket,
)
from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers.http_handlers import HTTPRouteHandler
from litestar.static_files.config import StaticFilesConfig

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("decorator", [get, post, patch, put, delete])
def test_indexes_handlers(decorator: Type[HTTPRouteHandler]) -> None:
    @decorator("/path-one/{param:str}", name="handler-name")  # type: ignore[call-arg]
    def handler() -> None:
        return None

    @asgi("/asgi-path", name="asgi-name")
    async def asgi_handler(scope: Any, receive: Any, send: Any) -> None:
        pass

    @websocket("/websocket-path", name="websocket-name")
    async def websocket_handler(socket: Any) -> None:
        pass

    router = Router("router-path/", route_handlers=[handler])
    app = Litestar(route_handlers=[router, websocket_handler, asgi_handler])

    handler_index = app.get_handler_index_by_name("handler-name")
    assert handler_index
    assert handler_index["paths"] == ["/router-path/path-one/{param:str}"]
    assert str(handler_index["handler"]) == str(handler)

    handler_index = app.get_handler_index_by_name("asgi-name")
    assert handler_index
    assert handler_index["paths"] == ["/asgi-path"]
    assert str(handler_index["handler"]) == str(asgi_handler)

    handler_index = app.get_handler_index_by_name("websocket-name")
    assert handler_index
    assert handler_index["paths"] == ["/websocket-path"]
    assert str(handler_index["handler"]) == str(websocket_handler)

    assert app.get_handler_index_by_name("nope") is None


@pytest.mark.parametrize("decorator", [get, post, patch, put, delete])
def test_default_indexes_handlers(decorator: Type[HTTPRouteHandler]) -> None:
    @decorator("/handler")  # type: ignore[call-arg]
    def handler() -> None:
        pass

    @decorator("/named_handler", name="named_handler")  # type: ignore[call-arg]
    def named_handler() -> None:
        pass

    class MyController(Controller):
        path = "/test"

        @decorator()  # type: ignore[call-arg]
        def handler(self) -> None:
            pass

    router = Router("router/", route_handlers=[handler, named_handler, MyController])
    app = Litestar(route_handlers=[router])

    handler_index = app.get_handler_index_by_name(str(handler))
    assert handler_index
    assert handler_index["paths"] == ["/router/handler"]
    assert str(handler_index["handler"]) == str(handler)
    assert handler_index["identifier"] == str(handler)

    handler_index = app.get_handler_index_by_name(str(MyController.handler))
    assert handler_index
    assert handler_index["paths"] == ["/router/test"]
    assert handler_index["identifier"] == str(MyController.handler)

    # check that default str(named_handler) does not override explicit name
    handler_index = app.get_handler_index_by_name(str(named_handler))
    assert handler_index is None


@pytest.mark.parametrize("decorator", [get, post, patch, put, delete])
def test_indexes_handlers_with_multiple_paths(decorator: Type[HTTPRouteHandler]) -> None:
    @decorator(["/path-one", "/path-one/{param:str}"], name="handler")  # type: ignore[call-arg]
    def handler() -> None:
        return None

    @decorator(["/path-two"], name="handler-two")  # type: ignore[call-arg]
    def handler_two() -> None:
        return None

    router = Router("router-one/", route_handlers=[handler_two])
    router_two = Router("router-two/", route_handlers=[handler_two])

    app = Litestar(route_handlers=[router, router_two, handler])

    handler_index = app.get_handler_index_by_name("handler")
    assert handler_index
    assert handler_index["paths"] == ["/path-one", "/path-one/{param:str}"]
    assert str(handler_index["handler"]) == str(handler)

    handler_index = app.get_handler_index_by_name("handler-two")
    assert handler_index
    assert handler_index["paths"] == ["/router-one/path-two", "/router-two/path-two"]
    assert str(handler_index["handler"]) == str(handler_two)


def test_indexing_validation(tmp_path: "Path") -> None:
    @get("/abc", name="same-name")
    def handler_one() -> None:
        pass

    @get("/xyz", name="same-name")
    def handler_two() -> None:
        pass

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[handler_one, handler_two])

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(
            route_handlers=[handler_one],
            static_files_config=[StaticFilesConfig(path="/static", directories=[tmp_path], name="same-name")],
        )
