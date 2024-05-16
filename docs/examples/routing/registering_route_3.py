from litestar import Litestar, get


@get()
def root_handler() -> None: ...


app = Litestar(route_handlers=[root_handler])


@get("/sub-path")
def sub_path_handler() -> None: ...


app.register(sub_path_handler)
