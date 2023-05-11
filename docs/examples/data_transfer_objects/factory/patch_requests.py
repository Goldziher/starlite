from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from litestar import Litestar, patch
from litestar.dto.factory import DTOConfig, DTOData
from litestar.dto.factory.stdlib.dataclass import DataclassDTO


@dataclass
class Person:
    id: UUID
    name: str
    age: int


class WriteDTO(DataclassDTO[Person]):
    """Don't allow client to set the id."""

    config = DTOConfig(exclude={"id"}, partial=True)


database = {
    UUID("f32ff2ce-e32f-4537-9dc0-26e7599f1380"): Person(
        id=UUID("f32ff2ce-e32f-4537-9dc0-26e7599f1380"), name="Peter", age=40
    )
}


@patch("/person/{person_id:uuid}", dto=WriteDTO, return_dto=None)
def update_person(person_id: UUID, data: DTOData[Person]) -> Person:
    """Create a person."""
    return data.update_instance(database.get(person_id))


app = Litestar(route_handlers=[update_person])

# run: /person/f32ff2ce-e32f-4537-9dc0-26e7599f1380 -X PATCH -H "Content-Type: application/json" -d '{"name":"Peter Pan"}'
