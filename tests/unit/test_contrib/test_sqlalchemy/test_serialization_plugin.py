from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.contrib.sqlalchemy.plugins import SQLAlchemySerializationPlugin
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from types import ModuleType
    from typing import Callable

    from litestar.testing import RequestFactory


async def test_serialization_plugin(
    create_module: Callable[[str], ModuleType], request_factory: RequestFactory
) -> None:
    module = create_module(
        """
from __future__ import annotations

from typing import List

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from litestar import Litestar, get, post
from litestar.contrib.sqlalchemy.plugins import SQLAlchemySerializationPlugin

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)

class A(Base):
    __tablename__ = "a"
    a: Mapped[str]

@post("/a")
def post_handler(data: A) -> A:
    return data

@get("/a")
def get_handler() -> List[A]:
    return [A(id=1, a="test"), A(id=2, a="test2")]

@get("/a/1")
def get_a() -> A:
    return A(id=1, a="test")
"""
    )
    with create_test_client(
        route_handlers=[module.post_handler, module.get_handler, module.get_a],
        plugins=[SQLAlchemySerializationPlugin()],
        debug=True,
    ) as client:
        response = client.post("/a", json={"id": 1, "a": "test"})
        assert response.status_code == 201
        assert response.json() == {"id": 1, "a": "test"}
        response = client.get("/a")
        assert response.json() == [{"id": 1, "a": "test"}, {"id": 2, "a": "test2"}]
        response = client.get("/a/1")
        assert response.json() == {"id": 1, "a": "test"}
