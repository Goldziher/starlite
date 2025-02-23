from litestar import Litestar, get


@get("/", sync_to_thread=False)
def index(param: str) -> dict[str, str]:
    return {"param": param}


app = Litestar(route_handlers=[index])

# run: /?param=foo
# run: /?param=bar
