from dataclasses import dataclass

from litestar import Litestar, post


@dataclass
class TodoItem:
    title: str
    done: bool


TODO_LIST: list[TodoItem] = []


@post("/")
async def add_item(data: TodoItem) -> list[TodoItem]:
    TODO_LIST.append(data)
    return TODO_LIST


app = Litestar([add_item])
