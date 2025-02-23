from typing import Any, Union

from litestar import Litestar, post

TODO_LIST: list[dict[str, Union[str, bool]]] = []


@post("/")
async def add_item(data: dict[str, Any]) -> list[dict[str, Union[str, bool]]]:
    TODO_LIST.append(data)
    return TODO_LIST


app = Litestar([add_item])
