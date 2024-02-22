from litestar import Litestar
from litestar.router import Router
from litestar.static_files import create_static_files_router


class MyRouter(Router):
    pass


app = Litestar(
    route_handlers=[
        create_static_files_router(
            path="/static",
            directories=["assets"],
            router_class=MyRouter,
        )
    ]
)
