from litestar import Litestar, Router, get


@get(path="/handler")
def my_route_handler() -> None: ...


internal_router = Router(path="/internal", route_handlers=[my_route_handler])
partner_router = Router(path="/partner", route_handlers=[my_route_handler])
consumer_router = Router(path="/consumer", route_handlers=[my_route_handler])

Litestar(route_handlers=[internal_router, partner_router, consumer_router])
