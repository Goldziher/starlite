from starlette.responses import JSONResponse

from litestar import get
from litestar.types import ASGIApp


@get("/")
def handler() -> ASGIApp:
    return JSONResponse(content={"hello": "world"})  # type: ignore
