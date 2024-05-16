from litestar import Request, get


@get("/")
def index(request: Request) -> None:
    print(request.method)
