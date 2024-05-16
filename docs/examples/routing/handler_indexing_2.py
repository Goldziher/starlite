from litestar import Request, get


@get(
    ["/some-path", "/some-path/{id:int}", "/some-path/{id:int}/{val:str}"],
    name="handler_name",
)
def handler(id: int = 1, val: str = "default") -> None: ...


@get("/path-info")
def path_info(request: Request) -> str:
    path_optional = request.app.route_reverse("handler_name")
    # /some-path`

    path_partial = request.app.route_reverse("handler_name", id=100)
    # /some-path/100

    path_full = request.app.route_reverse("handler_name", id=100, val="value")
    # /some-path/100/value`

    return f"{path_optional} {path_partial} {path_full}"
