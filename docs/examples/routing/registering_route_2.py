from litestar import Litestar, get


@get(["/", "/sub-path"])
def handler() -> None: ...


app = Litestar(route_handlers=[handler])
