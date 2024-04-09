from typing import TYPE_CHECKING, Any, Callable, Dict

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

if TYPE_CHECKING:
    from litestar import WebSocket
    from litestar.types import Receive, RouteHandlerType, Scope, Send


def regular_handler() -> None: ...


async def asgi_handler(scope: "Scope", receive: "Receive", send: "Send") -> None: ...


async def socket_handler(socket: "WebSocket") -> None: ...


@pytest.mark.parametrize(
    "decorator, handler",
    [
        (get, regular_handler),
        (post, regular_handler),
        (delete, regular_handler),
        (put, regular_handler),
        (patch, regular_handler),
        (asgi, asgi_handler),
        (websocket, socket_handler),
    ],
)
def test_opt_settings(decorator: "RouteHandlerType", handler: Callable) -> None:
    base_opt = {"base": 1, "kwarg_value": 0}
    result = decorator("/", opt=base_opt, kwarg_value=2)(handler)  # type: ignore[arg-type, call-arg]
    assert result.opt == {"base": 1, "kwarg_value": 2}


@pytest.mark.parametrize(
    "app_opt, router_opt, controller_opt, route_opt, expected_opt",
    [
        [
            {"app": "app"},
            {"router": "router"},
            {"controller": "controller"},
            {"route": "route"},
            {"app": "app", "router": "router", "controller": "controller", "route": "route"},
        ],
        [
            {"override": "app"},
            {"router": "router"},
            None,
            {"override": "route"},
            {"router": "router", "override": "route"},
        ],
        [None, None, None, None, {}],
    ],
)
def test_opt_resolution(
    app_opt: Dict[str, Any],
    router_opt: Dict[str, Any],
    controller_opt: Dict[str, Any],
    route_opt: Dict[str, Any],
    expected_opt: Dict[str, Any],
) -> None:
    class MyController(Controller):
        path = "/controller"
        opt = controller_opt

        @get(opt=route_opt)
        def handler(self) -> None: ...

    router = Router("/router", route_handlers=[MyController], opt=router_opt)
    app = Litestar(route_handlers=[router], opt=app_opt)
    assert (
        app.asgi_router.root_route_map_node.children["/router/controller"].asgi_handlers["GET"][1].opt == expected_opt
    )


def test_opt_not_affected_by_route_handler_copying() -> None:
    class MyController(Controller):
        path = "/controller"

        @get(opt={"route": "route"})
        def handler(self) -> None: ...

    @get("/fn_handler", opt={"fn_route": "fn_route"})
    def fn_handler() -> None: ...

    router = Router("/router", route_handlers=[MyController, fn_handler], opt={"router": "router"})
    another_router = Router("/another_router", route_handlers=[MyController, fn_handler])

    app = Litestar(route_handlers=[router, another_router])

    assert app.asgi_router.root_route_map_node.children["/router/controller"].asgi_handlers["GET"][1].opt == {
        "router": "router",
        "route": "route",
    }
    assert app.asgi_router.root_route_map_node.children["/router/fn_handler"].asgi_handlers["GET"][1].opt == {
        "router": "router",
        "fn_route": "fn_route",
    }

    assert app.asgi_router.root_route_map_node.children["/another_router/controller"].asgi_handlers["GET"][1].opt == {
        "route": "route",
    }

    assert app.asgi_router.root_route_map_node.children["/another_router/fn_handler"].asgi_handlers["GET"][1].opt == {
        "fn_route": "fn_route",
    }
