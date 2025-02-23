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
    websocket,
)
from litestar import (
    route as route_decorator,
)
from litestar.exceptions import ImproperlyConfiguredException
from litestar.routes import HTTPRoute


@pytest.fixture
def controller() -> type[Controller]:
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


def test_register_with_controller_class(controller: type[Controller]) -> None:
    router = Litestar(path="/base", route_handlers=[controller], openapi_config=None)
    assert len(router.routes) == 3
    for route in router.routes:
        if isinstance(route, HTTPRoute):
            if len(route.methods) == 2:
                assert sorted(route.methods) == sorted(["GET", "OPTIONS"])  # pyright: ignore
                assert route.path == "/base/test/{id:int}"
            elif len(route.methods) == 3:
                assert sorted(route.methods) == sorted(["GET", "POST", "OPTIONS"])  # pyright: ignore
                assert route.path == "/base/test"


def test_register_with_router_instance(controller: type[Controller]) -> None:
    top_level_router = Router(path="/top-level", route_handlers=[controller])
    base_router = Litestar(path="/base", route_handlers=[top_level_router], openapi_config=None)

    assert len(base_router.routes) == 3
    for route in base_router.routes:
        if isinstance(route, HTTPRoute):
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

    router = Litestar(
        path="/base",
        route_handlers=[first_route_handler, second_route_handler, third_route_handler],
        openapi_config=None,
    )
    assert len(router.routes) == 2
    for route in router.routes:
        if isinstance(route, HTTPRoute):
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
        Litestar(path="/base", route_handlers=[MyCustomClass])


def test_register_already_registered_router() -> None:
    first_router = Router(path="/first", route_handlers=[])
    Router(path="/second", route_handlers=[first_router])
    Router(path="/third", route_handlers=[first_router])


def test_register_router_on_itself() -> None:
    router = Router(path="/first", route_handlers=[])

    with pytest.raises(ImproperlyConfiguredException):
        router.register(router)


def test_register_app_on_itself() -> None:
    app = Litestar(path="/first", route_handlers=[])

    with pytest.raises(ImproperlyConfiguredException):
        app.register(app)


def test_missing_path_param_type(controller: type[Controller]) -> None:
    missing_path_type = "/missing_path_type/{path_type}"

    @get(path=missing_path_type)
    def handler() -> None: ...

    with pytest.raises(ImproperlyConfiguredException) as exc:
        Litestar(route_handlers=[handler])
    assert missing_path_type in exc.value.args[0]
