from litestar import Litestar, Router, get


@get("/{order_id:int}")
def order_handler(order_id: int) -> None: ...


order_router = Router(path="/orders", route_handlers=[order_handler])
base_router = Router(path="/base", route_handlers=[order_router])
app = Litestar(route_handlers=[base_router])
