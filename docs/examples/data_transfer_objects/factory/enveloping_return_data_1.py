from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class WithCount(Generic[T]):
    count: int
    data: List[T]
