from functools import partial
from typing import Any, Generic, TypeVar

import pytest

from litestar.utils.helpers import get_name, unique_name_for_scope, unwrap_partial

T = TypeVar("T")


class GenericFoo(Generic[T]): ...


class Foo: ...


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (Foo, "Foo"),
        (Foo(), "Foo"),
        (GenericFoo, "GenericFoo"),
        (GenericFoo[int], "GenericFoo"),
        (GenericFoo[T], "GenericFoo"),  # type: ignore[valid-type]
        (GenericFoo(), "GenericFoo"),
    ),
)
def test_get_name(value: Any, expected: str) -> None:
    assert get_name(value) == expected


def test_unwrap_partial() -> None:
    def func(*args: int) -> int:
        return sum(args)

    wrapped = partial(partial(partial(func, 1), 2))

    assert wrapped() == 3
    assert unwrap_partial(wrapped) is func


def test_unique_name_for_scope() -> None:
    assert unique_name_for_scope("a", []) == "a_0"

    assert unique_name_for_scope("a", ["a", "a_0", "b"]) == "a_1"

    assert unique_name_for_scope("b", ["a", "a_0", "b"]) == "b_0"
