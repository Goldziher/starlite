from litestar import get
from litestar.datastructures import State


@get("/")
def handler(state: State) -> None: ...
