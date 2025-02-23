from typing import Union

from litestar import Litestar, get

TODO_LIST: list[dict[str, Union[str, bool]]] = [
    {"title": "Start writing TODO list", "done": True},
    {"title": "???", "done": False},
    {"title": "Profit", "done": False},
]


@get("/")
async def get_list() -> list[dict[str, Union[str, bool]]]:
    return TODO_LIST


app = Litestar([get_list])
