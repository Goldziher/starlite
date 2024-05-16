from dataclasses import dataclass

from litestar.dto import DataclassDTO, DTOConfig


@dataclass
class Foo:
    name: str


class FooDTO(DataclassDTO[Foo]):
    config = DTOConfig(experimental_codegen_backend=False)
