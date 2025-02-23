from __future__ import annotations

from dataclasses import dataclass

from litestar import Litestar, get
from litestar.dto import DataclassDTO, DTOConfig


@dataclass
class Address:
    street: str
    city: str
    country: str


@dataclass
class Person:
    name: str
    age: int
    email: str
    address: Address
    children: list[Person]


class ReadDTO(DataclassDTO[Person]):
    config = DTOConfig(
        exclude={"email", "address.street", "children.0.email", "children.0.address"},
        max_nested_depth=2,
    )


@get("/person/{name:str}", return_dto=ReadDTO, sync_to_thread=False)
def get_person(name: str) -> Person:
    # Your logic to retrieve the person goes here
    # For demonstration purposes, a placeholder Person instance is returned
    address = Address(street="123 Main St", city="Cityville", country="Countryland")
    child1 = Person(name="Child1", age=10, email="child1@example.com", address=address, children=[])
    child2 = Person(name="Child2", age=8, email="child2@example.com", address=address, children=[])
    return Person(
        name=name,
        age=30,
        email=f"email_of_{name}@example.com",
        address=address,
        children=[child1, child2],
    )


app = Litestar(route_handlers=[get_person])
