from typing import Protocol, runtime_checkable

import pytest
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from litestar import get
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


class Item(BaseModel):
    name: str


@runtime_checkable
class Service(Protocol):
    def get_one(self) -> Item: ...


@get(path="/item")
def get_item(service: Service) -> Item:
    return service.get_one()


class ItemFactory(ModelFactory[Item]):
    model = Item


@pytest.fixture()
def item():
    return ItemFactory.build()


def test_get_item(item: Item):
    class MyService(Service):
        def get_one(self) -> Item:
            return item

    with create_test_client(route_handlers=get_item, dependencies={"service": Provide(lambda: MyService())}) as client:
        response = client.get("/item")
        assert response.status_code == HTTP_200_OK
        assert response.json() == item.dict()
