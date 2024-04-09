# ruff: noqa: UP007, UP006

from __future__ import annotations

from sys import version_info
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

import pytest
from typing_extensions import Annotated

from litestar.utils.typing import (
    expand_type_var_in_type_hint,
    get_origin_or_inner_type,
    get_type_hints_with_generics_resolved,
    make_non_optional_union,
)
from tests.models import DataclassPerson, DataclassPet  # noqa: F401

if version_info >= (3, 10):
    from collections import deque  # noqa: F401

    py_310_plus_annotation = [
        (eval(tp), exp)
        for tp, exp in [
            ("tuple[DataclassPerson, ...]", True),
            ("list[DataclassPerson]", True),
            ("deque[DataclassPerson]", True),
            ("tuple[DataclassPet, ...]", False),
            ("list[DataclassPet]", False),
            ("deque[DataclassPet]", False),
        ]
    ]
else:
    py_310_plus_annotation = []


@pytest.mark.parametrize(
    ("annotation", "expected"), [(Union[None, str, int], Union[str, int]), (Optional[Union[str, int]], Union[str, int])]
)
def test_make_non_optional_union(annotation: Any, expected: Any) -> None:
    assert make_non_optional_union(annotation) == expected


def test_get_origin_or_inner_type() -> None:
    assert get_origin_or_inner_type(List[DataclassPerson]) == list
    assert get_origin_or_inner_type(Annotated[List[DataclassPerson], "foo"]) == list
    assert get_origin_or_inner_type(Annotated[Dict[str, List[DataclassPerson]], "foo"]) == dict


T = TypeVar("T")
V = TypeVar("V", int, str)
U = TypeVar("U", bound=int)

ANNOTATION = object()


class Foo(Generic[T]):
    foo: T


class BoundFoo(Generic[U]):
    bound_foo: U


class ConstrainedFoo(Generic[V]):
    constrained_foo: V


class AnnotatedFoo(Generic[T]):
    annotated_foo: Annotated[T, ANNOTATION]


class UnionFoo(Generic[T, V, U]):
    union_foo: Union[T, bool]
    constrained_union_foo: Union[V, bool]
    bound_union_foo: Union[U, bool]


class MixedFoo(Generic[T]):
    foo: T
    list_foo: List[T]
    normal_foo: str
    normal_list_foo: List[str]


class NestedFoo(Generic[T]):
    bound_foo: BoundFoo
    constrained_foo: ConstrainedFoo
    constrained_foo_with_t: ConstrainedFoo[int]


@pytest.mark.parametrize(
    ("annotation", "expected_type_hints"),
    (
        (Foo[int], {"foo": int}),
        (BoundFoo, {"bound_foo": int}),
        (BoundFoo[int], {"bound_foo": int}),
        (ConstrainedFoo[int], {"constrained_foo": int}),
        (ConstrainedFoo, {"constrained_foo": Union[int, str]}),
        (AnnotatedFoo[int], {"annotated_foo": Annotated[int, ANNOTATION]}),
        (
            UnionFoo[T, V, U],  # type: ignore[valid-type]
            {
                "union_foo": Union[T, bool],  # pyright: ignore[reportGeneralTypeIssues]
                "constrained_union_foo": Union[int, str, bool],
                "bound_union_foo": Union[int, bool],
            },
        ),
        (
            UnionFoo,
            {
                "union_foo": Union[T, bool],  # pyright: ignore[reportGeneralTypeIssues]
                "constrained_union_foo": Union[int, str, bool],
                "bound_union_foo": Union[int, bool],
            },
        ),
        (
            MixedFoo[int],
            {
                "foo": int,
                "list_foo": List[int],
                "normal_foo": str,
                "normal_list_foo": List[str],
            },
        ),
        (
            NestedFoo[int],
            {
                "bound_foo": BoundFoo[int],
                "constrained_foo": ConstrainedFoo[Union[int, str]],  # type: ignore[type-var]
                "constrained_foo_with_t": ConstrainedFoo[int],
            },
        ),
    ),
)
def test_get_type_hints_with_generics(annotation: Any, expected_type_hints: dict[str, Any]) -> None:
    assert get_type_hints_with_generics_resolved(annotation, include_extras=True) == expected_type_hints


class ConcreteT: ...


@pytest.mark.parametrize(
    ("type_hint", "namespace", "expected"),
    (
        ({"arg1": T, "return": int}, {}, {"arg1": T, "return": int}),
        ({"arg1": T, "return": int}, None, {"arg1": T, "return": int}),
        ({"arg1": T, "return": int}, {U: ConcreteT}, {"arg1": T, "return": int}),
        ({"arg1": T, "return": int}, {T: ConcreteT}, {"arg1": ConcreteT, "return": int}),
        ({"arg1": T, "return": int}, {T: int}, {"arg1": int, "return": int}),
        ({"arg1": int, "return": int}, {}, {"arg1": int, "return": int}),
        ({"arg1": int, "return": int}, None, {"arg1": int, "return": int}),
        ({"arg1": int, "return": int}, {T: int}, {"arg1": int, "return": int}),
        ({"arg1": T, "return": T}, {T: ConcreteT}, {"arg1": ConcreteT, "return": ConcreteT}),
        ({"arg1": T, "return": T}, {T: int}, {"arg1": int, "return": int}),
    ),
)
def test_expand_type_var_in_type_hints(
    type_hint: dict[str, Any], namespace: dict[str, Any] | None, expected: dict[str, Any]
) -> None:
    assert expand_type_var_in_type_hint(type_hint, namespace) == expected
