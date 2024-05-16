from typing import Any

from litestar import Litestar, Request, get


@get("/some-path")
def route_handler(request: Request[Any, Any]) -> None:
    @get("/sub-path")
    def sub_path_handler() -> None: ...

    request.app.register(sub_path_handler)


app = Litestar(route_handlers=[route_handler])
