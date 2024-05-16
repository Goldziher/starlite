from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from litestar import get
from litestar.openapi.datastructures import ResponseSpec


class Item(BaseModel): ...


class ItemNotFound(BaseModel):
    was_removed: bool
    removed_at: Optional[datetime]


@get(
    path="/items/{pk:int}",
    responses={404: ResponseSpec(data_container=ItemNotFound, description="Item was removed or not found")},
)
def retrieve_item(pk: int) -> Item: ...
