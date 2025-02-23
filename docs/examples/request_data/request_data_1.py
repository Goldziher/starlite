from litestar import Litestar, post


@post(path="/")
async def index(data: dict[str, str]) -> dict[str, str]:
    return data


app = Litestar(route_handlers=[index])
