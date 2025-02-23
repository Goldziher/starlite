from typing import Annotated, Union

from litestar import Controller, Litestar, Router, get
from litestar.params import Parameter


class MyController(Controller):
    path = "/controller"
    parameters = {
        "controller_param": Parameter(int, lt=100),
    }

    @get("/{path_param:int}", sync_to_thread=False)
    def my_handler(
        self,
        path_param: int,
        local_param: str,
        router_param: str,
        controller_param: Annotated[int, Parameter(int, lt=50)],
    ) -> dict[str, Union[str, int]]:
        return {
            "path_param": path_param,
            "local_param": local_param,
            "router_param": router_param,
            "controller_param": controller_param,
        }


router = Router(
    path="/router",
    route_handlers=[MyController],
    parameters={
        "router_param": Parameter(str, pattern="^[a-zA-Z]$", header="MyHeader", required=False),
    },
)

app = Litestar(
    route_handlers=[router],
    parameters={
        "app_param": Parameter(str, cookie="special-cookie"),
    },
)
