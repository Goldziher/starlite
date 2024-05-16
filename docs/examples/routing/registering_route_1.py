from litestar import Litestar, get


@get("/sub-path")
def sub_path_handler() -> None: ...


@get()
def root_handler() -> None: ...


app = Litestar(route_handlers=[root_handler, sub_path_handler])
