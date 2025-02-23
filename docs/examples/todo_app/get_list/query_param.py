from dataclasses import dataclass

from litestar import Litestar, get


@dataclass
class TodoItem:
    title: str
    done: bool


TODO_LIST: list[TodoItem] = [
    TodoItem(title="Start writing TODO list", done=True),
    TodoItem(title="???", done=False),
    TodoItem(title="Profit", done=False),
]


@get("/")
async def get_list(done: str) -> list[TodoItem]:
    if done == "1":
        return [item for item in TODO_LIST if item.done]
    return [item for item in TODO_LIST if not item.done]


app = Litestar([get_list])
