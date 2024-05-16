from litestar import Litestar, MediaType, get


@get(path="/health-check", media_type=MediaType.TEXT)
def health_check() -> str:
    return "healthy"


app = Litestar(route_handlers=[health_check])
