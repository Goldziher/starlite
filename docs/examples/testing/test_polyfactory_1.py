from typing import Protocol, runtime_checkable

from polyfactory.factories.pydantic import BaseModel

from litestar import get


class Item(BaseModel):
    name: str


@runtime_checkable
class Service(Protocol):
    def get(self) -> Item: ...


@get(path="/item")
def get_item(service: Service) -> Item:
    return service.get()
