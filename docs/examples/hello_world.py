from litestar import Litestar, get


@get("/")
async def hello_world() -> dict[str, str]:
    """Handler function that returns a greeting dictionary."""
    return {"hello": "world"}


app = Litestar(route_handlers=[hello_world])

# run: /
