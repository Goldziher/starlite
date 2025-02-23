from typing import Any, Generic, TypeVar

import pytest
from pydantic import BaseModel

from litestar.plugins.pydantic.utils import pydantic_get_type_hints_with_generics_resolved

T = TypeVar("T")


class GenericPydanticModel(BaseModel, Generic[T]):
    foo: T


@pytest.mark.parametrize(
    ("annotation", "expected_type_hints"),
    (
        (GenericPydanticModel, {"foo": T}),
        (GenericPydanticModel[int], {"foo": int}),
    ),
)
def test_get_pydantic_type_hints_with_generics_resolved(annotation: Any, expected_type_hints: dict[str, Any]) -> None:
    type_hints = pydantic_get_type_hints_with_generics_resolved(annotation)

    # In Python 3.12 and Pydantic V1, `__slots__` is returned in `get_type_hints`.
    slots_type = type_hints.pop("__slots__", None)
    if slots_type is not None:
        assert slots_type == tuple[str, ...]

    assert type_hints == expected_type_hints
