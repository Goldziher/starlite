from litestar import Controller, Router, get


class MyController(Controller):
    path = "/controller"

    @get()
    def handler(self) -> None: ...


internal_router = Router(path="/internal", route_handlers=[MyController])
partner_router = Router(path="/partner", route_handlers=[MyController])
consumer_router = Router(path="/consumer", route_handlers=[MyController])
