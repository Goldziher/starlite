from litestar import Litestar, Provide, Router, get


async def route_dependency() -> bool: ...


async def nested_dependency() -> str: ...


async def router_dependency() -> int: ...


async def app_dependency(nested: str) -> int: ...


@get("/", dependencies={"val_route": Provide(route_dependency)})
async def handler(val_route: bool, val_router: int, val_nested: str, val_app: int) -> None: ...


router = Router(dependencies={"val_router": Provide(router_dependency)})
app = Litestar(
    route_handlers=[handler],
    dependencies={
        "val_app": Provide(app_dependency),
        "val_nested": Provide(nested_dependency),
    },
)
