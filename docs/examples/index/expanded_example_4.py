from my_app.controllers.user import UserController

from litestar import Litestar

app = Litestar(route_handlers=[UserController])
