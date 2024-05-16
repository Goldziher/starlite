from litestar import Controller, get
from litestar.di import Provide


def bool_fn() -> bool: ...


def dict_fn() -> dict: ...


class MyController(Controller):
    path = "/controller"
    # on the controller
    dependencies = {"some_dependency": Provide(dict_fn)}

    # on the route handler
    @get(path="/handler", dependencies={"some_dependency": Provide(bool_fn)})
    def my_route_handler(
        self,
        some_dependency: bool,
    ) -> None: ...
