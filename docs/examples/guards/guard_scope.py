from litestar import Controller, Litestar, Router
from litestar.connection import ASGIConnection
from litestar.handlers.base import BaseRouteHandler


def my_guard(connection: ASGIConnection, handler: BaseRouteHandler) -> None: ...


# controller
class UserController(Controller):
    path = "/user"
    guards = [my_guard]


# router
admin_router = Router(path="admin", route_handlers=[UserController], guards=[my_guard])

# app
app = Litestar(route_handlers=[admin_router], guards=[my_guard])
