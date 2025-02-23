from itertools import islice

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from litestar import Litestar, get
from litestar.pagination import AbstractSyncOffsetPaginator, OffsetPagination


class Person(BaseModel):
    id: str
    name: str


class PersonFactory(ModelFactory[Person]):
    __model__ = Person


# we will implement a paginator - the paginator must implement two methods 'get_total' and 'get_items'
# we would usually use a database for this, but for our case we will "fake" the dataset using a factory.


class PersonOffsetPaginator(AbstractSyncOffsetPaginator[Person]):
    def __init__(self) -> None:
        self.data = PersonFactory.batch(50)

    def get_total(self) -> int:
        return len(self.data)

    def get_items(self, limit: int, offset: int) -> list[Person]:
        return list(islice(islice(self.data, offset, None), limit))


paginator = PersonOffsetPaginator()


# we now create a regular handler. The handler will receive two query parameters - 'limit' and 'offset', which
# we will pass to the paginator.
@get("/people", sync_to_thread=False)
def people_handler(limit: int, offset: int) -> OffsetPagination[Person]:
    return paginator(limit=limit, offset=offset)


app = Litestar(route_handlers=[people_handler])
