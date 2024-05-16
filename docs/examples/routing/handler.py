from litestar import get


@get("/")
def greet() -> str:
    return "hello world"
