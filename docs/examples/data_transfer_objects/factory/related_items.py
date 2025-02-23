from __future__ import annotations

from typing import Annotated
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from litestar import Litestar, put
from litestar.dto import DTOConfig
from litestar.plugins.sqlalchemy import SQLAlchemyDTO

from .my_lib import Base


class A(Base):
    b_id: Mapped[UUID] = mapped_column(ForeignKey("b.id"))
    b: Mapped[B] = relationship(back_populates="a")


class B(Base):
    a: Mapped[A] = relationship(back_populates="b")


data_config = DTOConfig(max_nested_depth=0)
DataDTO = SQLAlchemyDTO[Annotated[A, data_config]]

# default config sets max_nested_depth to 1
ReturnDTO = SQLAlchemyDTO[A]


@put("/a", dto=DataDTO, return_dto=ReturnDTO, sync_to_thread=False)
def update_a(data: A) -> A:
    # this shows that "b" was not parsed out of the inbound data
    assert "b" not in vars(data)
    # Now we'll create an instance of B and assign it"
    # This includes a reference back to ``a`` which is not serialized in the return data
    # because default ``max_nested_depth`` is set to 1
    data.b = B(id=data.b_id, a=data)
    return data


app = Litestar(route_handlers=[update_a])

# run: /a -H "Content-Type: application/json" -X PUT -d '{"id": "6955e63c-c2bc-4707-8fa4-2144d1764746", "b_id": "9cf3518d-7e19-4215-9ec2-e056cac55bf7", "b": {"id": "9cf3518d-7e19-4215-9ec2-e056cac55bf7"}}'
