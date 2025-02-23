from typing import TYPE_CHECKING

from litestar import Controller, Litestar, Router, get
from litestar.datastructures import State
from litestar.middleware import MiddlewareProtocol

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Receive, Scope, Send


def create_test_middleware(middleware_id: int) -> type[MiddlewareProtocol]:
    class TestMiddleware(MiddlewareProtocol):
        def __init__(self, app: "ASGIApp") -> None:
            self.app = app

        async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
            litestar_app = scope["app"]
            litestar_app.state.setdefault("middleware_calls", [])
            litestar_app.state["middleware_calls"].append(middleware_id)
            await self.app(scope, receive, send)

    return TestMiddleware


class MyController(Controller):
    path = "/controller"
    middleware = [create_test_middleware(4), create_test_middleware(5)]

    @get(
        "/handler",
        middleware=[create_test_middleware(6), create_test_middleware(7)],
    )
    async def my_handler(self, state: State) -> list[int]:
        return state["middleware_calls"]


router = Router(
    path="/router",
    route_handlers=[MyController],
    middleware=[create_test_middleware(2), create_test_middleware(3)],
)

app = Litestar(
    route_handlers=[router],
    middleware=[create_test_middleware(0), create_test_middleware(1)],
)


# run: /router/controller/handler
