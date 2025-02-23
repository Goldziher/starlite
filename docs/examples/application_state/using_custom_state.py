from typing import Any

from litestar import Litestar, get
from litestar.datastructures import State


class MyState(State):
    count: int = 0

    def increment(self) -> None:
        self.count += 1


@get("/", sync_to_thread=False)
def handler(state: MyState) -> dict[str, Any]:
    state.increment()
    return state.dict()


app = Litestar(route_handlers=[handler])
