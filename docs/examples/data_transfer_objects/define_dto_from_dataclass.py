from dataclasses import dataclass

from litestar import get
from litestar.dto import DataclassDTO, DTOConfig


@dataclass
class MyType:
    some_field: str
    another_field: int


class MyDTO(DataclassDTO[MyType]):
    config = DTOConfig(exclude={"another_field"})


@get(dto=MyDTO)
async def handler() -> MyType:
    return MyType(some_field="some value", another_field=42)
