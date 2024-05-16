from litestar import Litestar, Request, get
from litestar.exceptions import NotFoundException
from litestar.response import Redirect


@get("/abc", name="one")
def handler_one() -> None:
    pass


@get("/xyz", name="two")
def handler_two() -> None:
    pass


@get("/def/{param:int}", name="three")
def handler_three(param: int) -> None:
    pass


@get("/{handler_name:str}", name="four")
def handler_four(request: Request, name: str) -> Redirect:
    handler_index = request.app.get_handler_index_by_name(name)
    if not handler_index:
        raise NotFoundException(f"no handler matching the name {name} was found")

    # handler_index == { "paths": ["/"], "handler": ..., "qualname": ... }
    # do something with the handler index below, e.g. send a redirect response to the handler, or access
    # handler.opt and some values stored there etc.

    return Redirect(path=handler_index[0])


@get("/redirect/{param_value:int}", name="five")
def handler_five(request: Request, param_value: int) -> Redirect:
    path = request.app.route_reverse("three", param=param_value)
    return Redirect(path=path)


app = Litestar(route_handlers=[handler_one, handler_two, handler_three])
