from dataclasses import dataclass
from uuid import UUID

from litestar.dto import DataclassDTO, DTOConfig


@dataclass
class User:
    first_name: str
    last_name: str
    id: UUID


class PartialUserDTO(DataclassDTO[User]):
    config = DTOConfig(exclude={"id"}, partial=True)
