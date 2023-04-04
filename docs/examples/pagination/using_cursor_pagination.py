from typing import List, Optional, Tuple

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from starlite import Starlite, get
from starlite.pagination import AbstractSyncCursorPaginator, CursorPagination


class Person(BaseModel):
    id: str
    name: str


class PersonFactory(ModelFactory[Person]):
    __model__ = Person


# we will implement a paginator - the paginator must implement the method 'get_items'.


class PersonCursorPaginator(AbstractSyncCursorPaginator[str, Person]):
    def __init__(self) -> None:
        self.data = PersonFactory.batch(50)

    def get_items(self, cursor: Optional[str], results_per_page: int) -> Tuple[List[Person], Optional[str]]:
        results = self.data[:results_per_page]
        return results, results[-1].id


paginator = PersonCursorPaginator()


# we now create a regular handler. The handler will receive a single query parameter - 'cursor', which
# we will pass to the paginator.
@get("/people")
def people_handler(cursor: Optional[str], results_per_page: int) -> CursorPagination[str, Person]:
    return paginator(cursor=cursor, results_per_page=results_per_page)


app = Starlite(route_handlers=[people_handler])
