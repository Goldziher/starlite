from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from litestar import Litestar, get
from litestar.pagination import AbstractSyncClassicPaginator, ClassicPagination


class Person(BaseModel):
    id: str
    name: str


class PersonFactory(ModelFactory[Person]):
    __model__ = Person


# we will implement a paginator - the paginator must implement two methods 'get_total' and 'get_items'
# we would usually use a database for this, but for our case we will "fake" the dataset using a factory.


class PersonClassicPaginator(AbstractSyncClassicPaginator[Person]):
    def __init__(self) -> None:
        self.data = PersonFactory.batch(50)

    def get_total(self, page_size: int) -> int:
        return round(len(self.data) / page_size)

    def get_items(self, page_size: int, current_page: int) -> list[Person]:
        return [self.data[i : i + page_size] for i in range(0, len(self.data), page_size)][current_page - 1]


paginator = PersonClassicPaginator()


# we now create a regular handler. The handler will receive two query parameters - 'page_size' and 'current_page', which
# we will pass to the paginator.
@get("/people", sync_to_thread=False)
def people_handler(page_size: int, current_page: int) -> ClassicPagination[Person]:
    return paginator(page_size=page_size, current_page=current_page)


app = Litestar(route_handlers=[people_handler])
