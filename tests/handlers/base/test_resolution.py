from typing import Awaitable, Callable

from litestar import Controller, Litestar, Router, get
from litestar.di import Provide


def test_resolve_dependencies_without_provide() -> None:
    async def foo() -> None:
        pass

    async def bar() -> None:
        pass

    @get(dependencies={"foo": foo, "bar": Provide(bar)})
    async def handler() -> None:
        pass

    assert handler.resolve_dependencies() == {"foo": Provide(foo), "bar": Provide(bar)}


def test_resolve_dependencies_without_provide_sync_to_thread_by_default() -> None:
    def foo() -> None:
        pass

    @get(dependencies={"foo": foo})
    async def handler() -> None:
        pass

    assert handler.resolve_dependencies()["foo"].sync_to_thread is True


def function_factory() -> Callable[[], Awaitable[None]]:
    async def func() -> None:
        return None

    return func


def test_resolve_from_layers() -> None:
    app_dependency = function_factory()
    router_dependency = function_factory()
    controller_dependency = function_factory()
    handler_dependency = function_factory()

    class MyController(Controller):
        path = "/controller"
        dependencies = {"controller": controller_dependency}

        @get("/handler", dependencies={"handler": handler_dependency})
        async def handler(self) -> None:
            pass

    router = Router("/router", route_handlers=[MyController], dependencies={"router": router_dependency})
    app = Litestar([router], dependencies={"app": app_dependency})

    handler = app.routes[0].route_handlers[0]  # type: ignore[union-attr]

    assert handler.resolve_dependencies() == {
        "app": Provide(app_dependency),
        "router": Provide(router_dependency),
        "controller": Provide(controller_dependency),
        "handler": Provide(handler_dependency),
    }
