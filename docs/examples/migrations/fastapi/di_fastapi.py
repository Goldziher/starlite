from fastapi import APIRouter, Depends, FastAPI


async def route_dependency() -> bool: ...


async def nested_dependency() -> str: ...


async def router_dependency() -> int: ...


async def app_dependency(data: str = Depends(nested_dependency)) -> int: ...


router = APIRouter(dependencies=[Depends(router_dependency)])
app = FastAPI(dependencies=[Depends(nested_dependency)])
app.include_router(router)


@app.get("/")
async def handler(
    val_route: bool = Depends(route_dependency),
    val_router: int = Depends(router_dependency),
    val_nested: str = Depends(nested_dependency),
    val_app: int = Depends(app_dependency),
) -> None: ...
