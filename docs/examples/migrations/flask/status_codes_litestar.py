from litestar import Litestar, Response, get


@get("/static", status_code=404)
def static_status() -> str:
    return "not found"


@get("/dynamic")
def dynamic_status() -> Response[str]:
    return Response("not found", status_code=404)


app = Litestar([static_status, dynamic_status])
