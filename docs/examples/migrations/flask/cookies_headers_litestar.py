from litestar import Litestar, get, Response
from litestar.datastructures import ResponseHeader, Cookie


@get(
    "/static",
    response_headers={"my-header": ResponseHeader(value="header-value")},
    response_cookies=[Cookie("my-cookie", "cookie-value")],
)
def static() -> str:
    # you can set headers and cookies when defining handlers
    ...


@get("/dynamic")
def dynamic() -> Response[str]:
    # or dynamically, by returning an instance of Response
    return Response(
        "hello",
        headers={"my-header": "header-value"},
        cookies=[Cookie("my-cookie", "cookie-value")],
    )