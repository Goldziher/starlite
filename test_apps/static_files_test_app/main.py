from pathlib import Path

from litestar import Litestar, get
from litestar.static_files.config import create_static_files_router


@get("/")
async def handler() -> dict[str, str]:
    return {"hello": "world"}


app = Litestar(
    route_handlers=[
        create_static_files_router(directories=[Path(__file__).parent / "public"], path="/", html_mode=True),
    ],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
