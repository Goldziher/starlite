from typing import Any

from litestar import Litestar, get
from litestar.datastructures import State


@get("/", sync_to_thread=False)
def handler(state: State) -> dict[str, Any]:
    return state.dict()


app = Litestar(route_handlers=[handler], state=State({"count": 100}))
