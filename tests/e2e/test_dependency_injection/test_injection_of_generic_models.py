from typing import Generic, Optional, TypeVar

from msgspec import Struct

from litestar import get
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client

T = TypeVar("T")


class Store(Struct, Generic[T]):
    """Abstract store."""

    model: type[T]

    def get(self, value_id: str) -> Optional[T]:
        raise NotImplementedError


class Item(Struct):
    name: str


class DictStore(Store[Item]):
    """In-memory store implementation."""

    def get(self, value_id: str) -> Optional[Item]:
        return None


async def get_item_store() -> DictStore:
    return DictStore(model=Item)


def test_generic_model_injection() -> None:
    @get("/")
    def root(store: DictStore) -> Optional[Item]:
        assert isinstance(store, DictStore)
        return store.get("0")

    with create_test_client(root, dependencies={"store": Provide(get_item_store, use_cache=True)}) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
