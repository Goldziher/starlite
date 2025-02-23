from collections.abc import Awaitable
from typing import Callable
from unittest.mock import AsyncMock

from litestar import Controller, Litestar, Router, get
from litestar.di import Provide
from litestar.params import Parameter


def test_resolve_dependencies_without_provide() -> None:
    async def foo() -> None:
        pass

    async def bar() -> None:
        pass

    @get(dependencies={"foo": foo, "bar": Provide(bar)})
    async def handler() -> None:
        pass

    assert handler.dependencies == {"foo": Provide(foo), "bar": Provide(bar)}


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

    assert handler.dependencies == {
        "app": Provide(app_dependency),
        "router": Provide(router_dependency),
        "controller": Provide(controller_dependency),
        "handler": Provide(handler_dependency),
    }


def test_resolve_type_encoders() -> None:
    @get("/", type_encoders={int: str})
    def handler() -> None:
        pass

    assert handler.resolve_type_encoders() == {int: str}


def test_resolve_type_decoders() -> None:
    type_decoders = [(lambda t: True, lambda v, t: t)]

    @get("/", type_decoders=type_decoders)
    def handler() -> None:
        pass

    assert handler.resolve_type_decoders() == type_decoders


def test_resolve_parameters() -> None:
    parameters = {"foo": Parameter()}

    @get("/")
    def handler() -> None:
        pass

    handler = handler.merge(Router("/", parameters=parameters, route_handlers=[]))
    assert handler.resolve_layered_parameters() == handler.parameter_field_definitions


def test_resolve_guards() -> None:
    guard = AsyncMock()

    @get("/", guards=[guard])
    def handler() -> None:
        pass

    assert handler.resolve_guards() == (guard,)


def test_resolve_dependencies() -> None:
    dependency = AsyncMock()

    @get("/", dependencies={"foo": dependency})
    def handler() -> None:
        pass

    assert handler.resolve_dependencies() == handler.dependencies


def test_resolve_middleware() -> None:
    middleware = AsyncMock()

    @get("/", middleware=[middleware])
    def handler() -> None:
        pass

    assert handler.resolve_middleware() == handler.middleware


def test_exception_handlers() -> None:
    exception_handler = AsyncMock()

    @get("/", exception_handlers={ValueError: exception_handler})
    def handler() -> None:
        pass

    assert handler.resolve_exception_handlers() == {ValueError: exception_handler}


def test_resolve_signature_namespace() -> None:
    namespace = {"foo": object()}

    @get("/", signature_namespace=namespace)
    def handler() -> None:
        pass

    assert handler.resolve_signature_namespace() == namespace
