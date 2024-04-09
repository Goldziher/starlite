from typing import Type

import pytest

from litestar import (
    Controller,
    HttpMethod,
    Litestar,
    Router,
    WebSocket,
    get,
    patch,
    post,
    put,
    websocket,
)
from litestar import route as route_decorator
from litestar.exceptions import ImproperlyConfiguredException


@pytest.fixture
def controller() -> Type[Controller]:
    class MyController(Controller):
        path = "/test"

        @post(include_in_schema=False)
        def post_method(self) -> None:
            pass

        @get()
        def get_method(self) -> None:
            pass

        @get(path="/{id:int}")
        def get_by_id_method(self) -> None:
            pass

        @websocket(path="/socket")
        async def ws(self, socket: WebSocket) -> None:
            pass

    return MyController


def test_register_with_controller_class(controller: Type[Controller]) -> None:
    router = Router(path="/base", route_handlers=[controller])
    assert len(router.routes) == 3
    for route in router.routes:
        if len(route.methods) == 2:
            assert sorted(route.methods) == sorted(["GET", "OPTIONS"])  # pyright: ignore
            assert route.path == "/base/test/{id:int}"
        elif len(route.methods) == 3:
            assert sorted(route.methods) == sorted(["GET", "POST", "OPTIONS"])  # pyright: ignore
            assert route.path == "/base/test"


def test_register_controller_on_different_routers(controller: Type[Controller]) -> None:
    first_router = Router(path="/first", route_handlers=[controller])
    second_router = Router(path="/second", route_handlers=[controller])
    third_router = Router(path="/third", route_handlers=[controller])

    for router in (first_router, second_router, third_router):
        for route in router.routes:
            if hasattr(route, "route_handlers"):
                for route_handler in [
                    handler
                    for handler in route.route_handlers  # pyright: ignore
                    if handler.handler_name != "options_handler"
                ]:
                    assert route_handler.owner is not None
                    assert route_handler.owner.owner is not None
                    assert route_handler.owner.owner is router
            else:
                assert route.route_handler.owner is not None  # pyright: ignore
                assert route.route_handler.owner.owner is not None  # pyright: ignore
                assert route.route_handler.owner.owner is router  # pyright: ignore


def test_register_with_router_instance(controller: Type[Controller]) -> None:
    top_level_router = Router(path="/top-level", route_handlers=[controller])
    base_router = Router(path="/base", route_handlers=[top_level_router])

    assert len(base_router.routes) == 3
    for route in base_router.routes:
        if len(route.methods) == 2:
            assert sorted(route.methods) == sorted(["GET", "OPTIONS"])  # pyright: ignore
            assert route.path == "/base/top-level/test/{id:int}"
        elif len(route.methods) == 3:
            assert sorted(route.methods) == sorted(["GET", "POST", "OPTIONS"])  # pyright: ignore
            assert route.path == "/base/top-level/test"


def test_register_with_route_handler_functions() -> None:
    @route_decorator(path="/first", http_method=[HttpMethod.GET, HttpMethod.POST], status_code=200)
    def first_route_handler() -> None:
        pass

    @get(path="/second")
    def second_route_handler() -> None:
        pass

    @patch(path="/first")
    def third_route_handler() -> None:
        pass

    router = Router(path="/base", route_handlers=[first_route_handler, second_route_handler, third_route_handler])
    assert len(router.routes) == 2
    for route in router.routes:
        if len(route.methods) == 2:
            assert sorted(route.methods) == sorted(["GET", "OPTIONS"])  # pyright: ignore
            assert route.path == "/base/second"
        else:
            assert sorted(route.methods) == sorted(["GET", "POST", "PATCH", "OPTIONS"])  # pyright: ignore
            assert route.path == "/base/first"
            assert route.path == "/base/first"


def test_register_validation_wrong_class() -> None:
    class MyCustomClass:
        @get(path="/first")
        def first_route_handler(self) -> None:
            pass

        @get(path="/first")
        def second_route_handler(self) -> None:
            pass

    with pytest.raises(ImproperlyConfiguredException):
        Router(path="/base", route_handlers=[MyCustomClass])


def test_register_already_registered_router() -> None:
    first_router = Router(path="/first", route_handlers=[])
    Router(path="/second", route_handlers=[first_router])
    Router(path="/third", route_handlers=[first_router])


def test_register_router_on_itself() -> None:
    router = Router(path="/first", route_handlers=[])

    with pytest.raises(ImproperlyConfiguredException):
        router.register(router)


def test_route_handler_method_view(controller: Type[Controller]) -> None:
    @get(path="/root")
    def handler() -> None: ...

    def _handler() -> None: ...

    put_handler = put("/modify")(_handler)
    post_handler = post("/send")(_handler)

    first_router = Router(path="/first", route_handlers=[controller, post_handler, put_handler])
    second_router = Router(path="/second", route_handlers=[controller, post_handler, put_handler])

    app = Litestar(route_handlers=[first_router, second_router, handler])

    assert app.route_handler_method_view[str(handler)] == ["/root"]
    assert app.route_handler_method_view[str(controller.get_method)] == [  # type: ignore[attr-defined]
        "/first/test",
        "/second/test",
    ]

    assert app.route_handler_method_view[str(controller.ws)] == [  # type: ignore[attr-defined]
        "/first/test/socket",
        "/second/test/socket",
    ]
    assert app.route_handler_method_view[str(put_handler)] == [
        "/first/send",
        "/first/modify",
        "/second/send",
        "/second/modify",
    ]
    assert app.route_handler_method_view[str(post_handler)] == [
        "/first/send",
        "/first/modify",
        "/second/send",
        "/second/modify",
    ]


def test_missing_path_param_type(controller: Type[Controller]) -> None:
    missing_path_type = "/missing_path_type/{path_type}"

    @get(path=missing_path_type)
    def handler() -> None: ...

    with pytest.raises(ImproperlyConfiguredException) as exc:
        Router(path="/", route_handlers=[handler])
    assert missing_path_type in exc.value.args[0]
