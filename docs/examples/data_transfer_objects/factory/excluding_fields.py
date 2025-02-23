from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from litestar import Litestar, post
from litestar.dto import DTOConfig, dto_field
from litestar.plugins.sqlalchemy import SQLAlchemyDTO

from .my_lib import Base


class Address(Base):
    street: Mapped[str]
    city: Mapped[str]
    state: Mapped[str]
    zip: Mapped[str]


class Pets(Base):
    name: Mapped[str]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))


class User(Base):
    name: Mapped[str]
    password: Mapped[str] = mapped_column(info=dto_field("private"))
    created_at: Mapped[datetime] = mapped_column(info=dto_field("read-only"))
    address_id: Mapped[UUID] = mapped_column(ForeignKey("address.id"), info=dto_field("private"))
    address: Mapped[Address] = relationship(info=dto_field("read-only"))
    pets: Mapped[list[Pets]] = relationship(info=dto_field("read-only"))


UserDTO = SQLAlchemyDTO[User]
config = DTOConfig(
    exclude={
        "id",
        "address.id",
        "address.street",
        "pets.0.id",
        "pets.0.user_id",
    }
)
ReadUserDTO = SQLAlchemyDTO[Annotated[User, config]]


@post("/users", dto=UserDTO, return_dto=ReadUserDTO, sync_to_thread=False)
def create_user(data: User) -> User:
    data.created_at = datetime.min
    data.address = Address(street="123 Main St", city="Anytown", state="NY", zip="12345")
    data.pets = [Pets(id=1, name="Fido"), Pets(id=2, name="Spot")]
    return data


app = Litestar(route_handlers=[create_user])

# run: /users -H "Content-Type: application/json" -d '{"name":"Litestar User","password":"xyz","created_at":"2023-04-24T00:00:00Z"}'
