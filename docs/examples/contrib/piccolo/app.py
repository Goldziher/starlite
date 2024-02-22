from typing import List

from piccolo.columns import Boolean, Varchar
from piccolo.table import Table, create_db_tables

from litestar import Litestar, MediaType, delete, get, patch, post
from litestar.contrib.piccolo import PiccoloDTO
from litestar.dto import DTOConfig, DTOData
from litestar.exceptions import NotFoundException

from .piccolo_conf import DB


class Task(Table, db=DB):
    """
    An example table.
    """

    name = Varchar()
    completed = Boolean(default=False)


class PatchDTO(PiccoloDTO[Task]):
    """Allow partial updates."""

    config = DTOConfig(exclude={"id"}, partial=True)


@get(
    "/tasks",
    return_dto=PiccoloDTO[Task],
    media_type=MediaType.JSON,
    tags=["Task"],
)
async def tasks() -> List[Task]:
    return await Task.select().order_by(Task.id, ascending=False)


@post(
    "/tasks",
    dto=PiccoloDTO[Task],
    return_dto=PiccoloDTO[Task],
    media_type=MediaType.JSON,
    tags=["Task"],
)
async def create_task(data: Task) -> Task:
    await data.save()
    await data.refresh()
    return data


@patch(
    "/tasks/{task_id:int}",
    dto=PatchDTO,
    return_dto=PiccoloDTO[Task],
    media_type=MediaType.JSON,
    tags=["Task"],
)
async def update_task(task_id: int, data: DTOData[Task]) -> Task:
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        raise NotFoundException("Task does not exist")
    result = data.update_instance(task)
    await result.save()
    return result


@delete("/tasks/{task_id:int}", tags=["Task"])
async def delete_task(task_id: int) -> None:
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        raise NotFoundException("Task does not exist")
    await task.remove()


async def on_startup():
    await create_db_tables(Task, if_not_exists=True)


app = Litestar(route_handlers=[tasks, create_task, delete_task, update_task], on_startup=[on_startup], debug=True)
