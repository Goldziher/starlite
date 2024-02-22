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

        @get("/handler", dependencies={"handler": handler_dependency}, name="foo")
        async def handler(self) -> None:
            pass

    router = Router("/router", route_handlers=[MyController], dependencies={"router": router_dependency})
    app = Litestar([router], dependencies={"app": app_dependency}, openapi_config=None)

    handler_map = app.get_handler_index_by_name("foo")
    assert handler_map
    handler = handler_map["handler"]

    assert handler.resolve_dependencies() == {
        "app": Provide(app_dependency),
        "router": Provide(router_dependency),
        "controller": Provide(controller_dependency),
        "handler": Provide(handler_dependency),
    }


def test_resolve_dependencies_cached() -> None:
    dependency = Provide(function_factory())

    @get(dependencies={"foo": dependency})
    async def handler() -> None:
        pass

    @get(dependencies={"foo": dependency})
    async def handler_2() -> None:
        pass

    assert handler.resolve_dependencies() is handler.resolve_dependencies()
    assert handler_2.resolve_dependencies() is handler_2.resolve_dependencies()
