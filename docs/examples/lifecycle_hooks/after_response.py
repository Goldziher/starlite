from collections import defaultdict

from litestar import Litestar, Request, get

COUNTER: dict[str, int] = defaultdict(int)


async def after_response(request: Request) -> None:
    COUNTER[request.url.path] += 1


@get("/hello")
async def hello() -> dict[str, int]:
    return COUNTER


app = Litestar(route_handlers=[hello], after_response=after_response)


# run: /hello
# run: /hello
