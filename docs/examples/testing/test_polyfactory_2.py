import pytest
from my_app.main import Item, Service, get_item

from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


@pytest.fixture()
def item():
    return Item(name="Chair")


def test_get_item(item: Item):
    class MyService(Service):
        def get_one(self) -> Item:
            return item

    with create_test_client(route_handlers=get_item, dependencies={"service": Provide(lambda: MyService())}) as client:
        response = client.get("/item")
        assert response.status_code == HTTP_200_OK
        assert response.json() == item.dict()
