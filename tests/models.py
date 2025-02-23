import dataclasses
from enum import Enum
from typing import Optional
from uuid import UUID

import msgspec
from polyfactory.factories import DataclassFactory
from typing_extensions import NotRequired, Required, TypedDict


class Species(str, Enum):
    DOG = "Dog"
    CAT = "Cat"
    MONKEY = "Monkey"
    PIG = "Pig"


@dataclasses.dataclass
class DataclassPet:
    name: str
    age: float
    species: Species = Species.MONKEY


@dataclasses.dataclass
class DataclassPerson:
    first_name: str
    last_name: str
    id: str
    optional: Optional[str]
    complex: dict[str, list[dict[str, str]]]
    pets: Optional[list[DataclassPet]] = None


class TypedDictPerson(TypedDict):
    first_name: Required[str]
    last_name: Required[str]
    id: Required[str]
    optional: NotRequired[Optional[str]]
    complex: Required[dict[str, list[dict[str, str]]]]
    pets: NotRequired[Optional[list[DataclassPet]]]


class MsgSpecStructPerson(msgspec.Struct):
    first_name: str
    last_name: str
    id: str
    optional: Optional[str]
    complex: dict[str, list[dict[str, str]]]
    pets: Optional[list[DataclassPet]]


@dataclasses.dataclass
class User:
    name: str
    id: UUID


class UserFactory(DataclassFactory[User]):
    __model__ = User


class DataclassPersonFactory(DataclassFactory[DataclassPerson]):
    __model__ = DataclassPerson


class DataclassPetFactory(DataclassFactory[DataclassPet]):
    __model__ = DataclassPet
