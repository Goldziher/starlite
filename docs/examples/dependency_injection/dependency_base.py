from litestar import Controller, Litestar, Router, get
from litestar.di import Provide


async def bool_fn() -> bool: ...


async def dict_fn() -> dict: ...


async def list_fn() -> list: ...


async def int_fn() -> int: ...


class MyController(Controller):
    path = "/controller"
    # on the controller
    dependencies = {"controller_dependency": Provide(list_fn)}

    # on the route handler
    @get(path="/handler", dependencies={"local_dependency": Provide(int_fn)})
    def my_route_handler(
        self,
        app_dependency: bool,
        router_dependency: dict,
        controller_dependency: list,
        local_dependency: int,
    ) -> None: ...

    # on the router


my_router = Router(
    path="/router",
    dependencies={"router_dependency": Provide(dict_fn)},
    route_handlers=[MyController],
)

# on the app
app = Litestar(route_handlers=[my_router], dependencies={"app_dependency": Provide(bool_fn)})
