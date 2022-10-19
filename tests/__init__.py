from dataclasses import dataclass as vanilla_dataclass
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic_factories import ModelFactory
from typing_extensions import TypedDict


class Species(str, Enum):
    DOG = "Dog"
    CAT = "Cat"
    MONKEY = "Monkey"
    PIG = "Pig"


class Pet(BaseModel):
    name: str
    species: Species = Field(default=Species.MONKEY)
    age: float


class Person(BaseModel):
    first_name: str
    last_name: str
    id: str
    optional: Optional[str]
    complex: Dict[str, List[Dict[str, str]]]
    pets: Optional[List[Pet]] = None


class PersonFactory(ModelFactory[Person]):
    __model__ = Person


class PetFactory(ModelFactory[Pet]):
    __model__ = Pet


@vanilla_dataclass
class VanillaDataClassPerson:
    first_name: str
    last_name: str
    id: str
    optional: Optional[str]
    complex: Dict[str, List[Dict[str, str]]]
    pets: Optional[List[Pet]] = None


@pydantic_dataclass
class PydanticDataClassPerson:
    first_name: str
    last_name: str
    id: str
    optional: Optional[str]
    complex: Dict[str, List[Dict[str, str]]]
    pets: Optional[List[Pet]] = None


class TypedDictPerson(TypedDict):
    first_name: str
    last_name: str
    id: str
    optional: Optional[str]
    complex: Dict[str, List[Dict[str, str]]]
    pets: Optional[List[Pet]]
