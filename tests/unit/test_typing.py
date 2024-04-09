from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, ForwardRef, Generic, List, Optional, Tuple, TypeVar, Union

import annotated_types
import msgspec
import pytest
from typing_extensions import Annotated, NotRequired, Required, TypedDict, get_type_hints

from litestar.exceptions import LitestarWarning
from litestar.params import DependencyKwarg, KwargDefinition, Parameter, ParameterKwarg
from litestar.typing import FieldDefinition, _unpack_predicate

from .test_utils.test_signature import T, _check_field_definition, field_definition_int, test_type_hints


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        (
            int,
            {
                "raw": int,
                "annotation": int,
                "origin": None,
                "args": (),
                "metadata": (),
                "safe_generic_origin": None,
                "inner_types": (),
            },
        ),
        (
            List[int],
            {
                "raw": List[int],
                "annotation": List[int],
                "origin": list,
                "args": (int,),
                "metadata": (),
                "safe_generic_origin": List,
                "inner_types": (field_definition_int,),
            },
        ),
        (
            Annotated[int, "foo"],
            {
                "raw": Annotated[int, "foo"],
                "annotation": int,
                "origin": None,
                "args": (),
                "metadata": ("foo",),
                "safe_generic_origin": None,
                "inner_types": (),
            },
        ),
        (
            Annotated[List[int], "foo"],
            {
                "raw": Annotated[List[int], "foo"],
                "annotation": List[int],
                "origin": list,
                "args": (int,),
                "metadata": ("foo",),
                "safe_generic_origin": List,
                "inner_types": (field_definition_int,),
            },
        ),
        (
            test_type_hints["req_int"],
            {
                "raw": test_type_hints["req_int"],
                "annotation": int,
                "origin": None,
                "args": (),
                "metadata": (),
                "safe_generic_origin": None,
                "inner_types": (),
            },
        ),
        (
            test_type_hints["req_list_int"],
            {
                "raw": test_type_hints["req_list_int"],
                "annotation": List[int],
                "origin": list,
                "args": (int,),
                "metadata": (),
                "safe_generic_origin": List,
                "inner_types": (field_definition_int,),
            },
        ),
        (
            test_type_hints["not_req_int"],
            {
                "raw": test_type_hints["not_req_int"],
                "annotation": int,
                "origin": None,
                "args": (),
                "metadata": (),
                "safe_generic_origin": None,
                "inner_types": (),
            },
        ),
        (
            test_type_hints["not_req_list_int"],
            {
                "raw": test_type_hints["not_req_list_int"],
                "annotation": List[int],
                "origin": list,
                "args": (int,),
                "metadata": (),
                "safe_generic_origin": List,
                "inner_types": (field_definition_int,),
            },
        ),
        (
            test_type_hints["ann_req_int"],
            {
                "raw": test_type_hints["ann_req_int"],
                "annotation": int,
                "origin": None,
                "args": (),
                "metadata": ("foo",),
                "safe_generic_origin": None,
                "inner_types": (),
            },
        ),
        (
            test_type_hints["ann_req_list_int"],
            {
                "raw": test_type_hints["ann_req_list_int"],
                "annotation": List[int],
                "origin": list,
                "args": (int,),
                "metadata": ("foo",),
                "safe_generic_origin": List,
                "inner_types": (field_definition_int,),
            },
        ),
    ],
)
def test_field_definition_from_annotation(annotation: Any, expected: dict[str, Any]) -> None:
    """Test FieldDefinition.from_annotation."""
    _check_field_definition(FieldDefinition.from_annotation(annotation), expected)


def test_field_definition_kwarg_definition_from_extras() -> None:
    kwarg_definition = KwargDefinition()
    assert (
        FieldDefinition.from_annotation(int, extra={"kwarg_definition": kwarg_definition}).kwarg_definition
        is kwarg_definition
    )


@pytest.mark.parametrize("kwarg_definition", [KwargDefinition(), DependencyKwarg()])
def test_field_definition_kwarg_definition_from_kwargs(kwarg_definition: KwargDefinition | DependencyKwarg) -> None:
    assert FieldDefinition.from_annotation(int, kwarg_definition=kwarg_definition).kwarg_definition is kwarg_definition


def test_field_definition_with_annotated_kwarg_definition() -> None:
    kwarg_definition = KwargDefinition()
    fd = FieldDefinition.from_annotation(Annotated[str, kwarg_definition])
    assert fd.kwarg_definition is kwarg_definition


def test_field_definition_from_union_annotation() -> None:
    """Test FieldDefinition.from_annotation for Union."""
    annotation = Union[int, List[int]]
    expected = {
        "raw": annotation,
        "annotation": annotation,
        "origin": Union,
        "args": (int, List[int]),
        "metadata": (),
        "safe_generic_origin": Union,
        "inner_types": (FieldDefinition.from_annotation(int), FieldDefinition.from_annotation(List[int])),
    }
    _check_field_definition(FieldDefinition.from_annotation(annotation), expected)


@pytest.mark.parametrize("value", ["int", ForwardRef("int")])
def test_field_definition_is_forward_ref_predicate(value: Any) -> None:
    """Test FieldDefinition with ForwardRef."""
    field_definition = FieldDefinition.from_annotation(value)
    assert field_definition.is_forward_ref is True
    assert field_definition.annotation == value
    assert field_definition.origin is None
    assert field_definition.args == ()
    assert field_definition.metadata == ()
    assert field_definition.is_annotated is False
    assert field_definition.is_required is True
    assert field_definition.safe_generic_origin is None
    assert field_definition.inner_types == ()


def test_field_definition_is_type_var_predicate() -> None:
    """Test FieldDefinition.is_type_var."""
    assert FieldDefinition.from_annotation(int).is_type_var is False
    assert FieldDefinition.from_annotation(T).is_type_var is True
    assert FieldDefinition.from_annotation(Union[int, T]).is_type_var is False  # pyright: ignore


def test_field_definition_is_union_predicate() -> None:
    """Test FieldDefinition.is_union."""
    assert FieldDefinition.from_annotation(int).is_union is False
    assert FieldDefinition.from_annotation(Optional[int]).is_union is True
    assert FieldDefinition.from_annotation(Union[int, None]).is_union is True
    assert FieldDefinition.from_annotation(Union[int, str]).is_union is True


def test_field_definition_is_optional_predicate() -> None:
    """Test FieldDefinition.is_optional."""
    assert FieldDefinition.from_annotation(int).is_optional is False
    assert FieldDefinition.from_annotation(Optional[int]).is_optional is True
    assert FieldDefinition.from_annotation(Union[int, None]).is_optional is True
    assert FieldDefinition.from_annotation(Union[int, None, str]).is_optional is True
    assert FieldDefinition.from_annotation(Union[int, str]).is_optional is False


def test_field_definition_is_dataclass_predicate() -> None:
    """Test FieldDefinition.is_dataclass."""

    class NormalClass: ...

    @dataclass
    class NormalDataclass: ...

    @dataclass
    class GenericDataclass(Generic[T]): ...

    assert FieldDefinition.from_annotation(NormalDataclass).is_dataclass_type is True
    assert FieldDefinition.from_annotation(GenericDataclass).is_dataclass_type is True
    assert FieldDefinition.from_annotation(GenericDataclass[int]).is_dataclass_type is True
    assert FieldDefinition.from_annotation(GenericDataclass[T]).is_dataclass_type is True  # type: ignore[valid-type]
    assert FieldDefinition.from_annotation(NormalClass).is_dataclass_type is False


def test_field_definition_is_typeddict_predicate() -> None:
    """Test FieldDefinition.is_typeddict."""

    class NormalClass: ...

    class TypedDictClass(TypedDict): ...

    assert FieldDefinition.from_annotation(NormalClass).is_typeddict_type is False
    assert FieldDefinition.from_annotation(TypedDictClass).is_typeddict_type is True

    if sys.version_info >= (3, 11):

        class GenericTypedDictClass(TypedDict, Generic[T]): ...

        assert FieldDefinition.from_annotation(GenericTypedDictClass).is_typeddict_type is True
        assert FieldDefinition.from_annotation(GenericTypedDictClass[int]).is_typeddict_type is True
        assert FieldDefinition.from_annotation(GenericTypedDictClass[T]).is_typeddict_type is True


def test_field_definition_is_subclass_of() -> None:
    """Test FieldDefinition.is_type_of."""
    assert FieldDefinition.from_annotation(bool).is_subclass_of(int) is True
    assert FieldDefinition.from_annotation(bool).is_subclass_of(str) is False
    assert FieldDefinition.from_annotation(Union[int, str]).is_subclass_of(int) is False
    assert FieldDefinition.from_annotation(List[int]).is_subclass_of(list) is True
    assert FieldDefinition.from_annotation(List[int]).is_subclass_of(int) is False
    assert FieldDefinition.from_annotation(Optional[int]).is_subclass_of(int) is False
    assert FieldDefinition.from_annotation(Union[bool, int]).is_subclass_of(int) is True


def test_field_definition_has_inner_subclass_of() -> None:
    """Test FieldDefinition.has_type_of."""
    assert FieldDefinition.from_annotation(List[int]).has_inner_subclass_of(int) is True
    assert FieldDefinition.from_annotation(List[int]).has_inner_subclass_of(str) is False
    assert FieldDefinition.from_annotation(List[Union[int, str]]).has_inner_subclass_of(int) is False


def test_field_definition_equality() -> None:
    assert FieldDefinition.from_annotation(int) == FieldDefinition.from_annotation(int)
    assert FieldDefinition.from_annotation(int) == FieldDefinition.from_annotation(Annotated[int, "meta"])
    assert FieldDefinition.from_annotation(int) != int
    assert FieldDefinition.from_annotation(List[int]) == FieldDefinition.from_annotation(List[int])
    assert FieldDefinition.from_annotation(List[int]) != FieldDefinition.from_annotation(List[str])
    assert FieldDefinition.from_annotation(List[str]) != FieldDefinition.from_annotation(Tuple[str])
    assert FieldDefinition.from_annotation(Optional[str]) == FieldDefinition.from_annotation(Union[str, None])


def test_field_definition_hash() -> None:
    assert hash(FieldDefinition.from_annotation(int)) == hash(FieldDefinition.from_annotation(int))
    assert hash(FieldDefinition.from_annotation(Annotated[int, False])) == hash(
        FieldDefinition.from_annotation(Annotated[int, False])
    )
    assert hash(FieldDefinition.from_annotation(Annotated[int, False])) != hash(
        FieldDefinition.from_annotation(Annotated[int, True])
    )
    assert hash(FieldDefinition.from_annotation(Union[str, int])) != hash(
        FieldDefinition.from_annotation(Union[int, str])
    )


def test_is_required() -> None:
    class Foo(TypedDict):
        required: Required[str]
        not_required: NotRequired[str]

    class Bar(msgspec.Struct):
        unset: Union[str, msgspec.UnsetType] = msgspec.UNSET  # noqa: UP007
        with_default: str = ""
        with_none_default: Union[str, None] = None  # noqa: UP007

    assert FieldDefinition.from_annotation(get_type_hints(Foo, include_extras=True)["required"]).is_required is True
    assert (
        FieldDefinition.from_annotation(get_type_hints(Foo, include_extras=True)["not_required"]).is_required is False
    )
    assert FieldDefinition.from_annotation(get_type_hints(Bar, include_extras=True)["unset"]).is_required is False

    assert (
        FieldDefinition.from_kwarg(
            name="foo", kwarg_definition=ParameterKwarg(required=False), annotation=str
        ).is_required
        is False
    )
    assert (
        FieldDefinition.from_kwarg(
            name="foo", kwarg_definition=ParameterKwarg(required=True), annotation=str
        ).is_required
        is True
    )
    assert (
        FieldDefinition.from_kwarg(
            name="foo", kwarg_definition=ParameterKwarg(required=None, default=""), annotation=str
        ).is_required
        is False
    )
    assert (
        FieldDefinition.from_kwarg(
            name="foo", kwarg_definition=ParameterKwarg(required=None), annotation=str
        ).is_required
        is True
    )

    assert FieldDefinition.from_annotation(Optional[str]).is_required is False
    assert FieldDefinition.from_annotation(str).is_required is True

    assert FieldDefinition.from_annotation(Any).is_required is False

    assert FieldDefinition.from_annotation(get_type_hints(Bar)["with_default"]).is_required is True
    assert FieldDefinition.from_annotation(get_type_hints(Bar)["with_none_default"]).is_required is False


def test_field_definition_bound_type() -> None:
    class Foo:
        pass

    class Bar:
        pass

    bound = TypeVar("bound", bound=Foo)
    multiple_bounds = TypeVar("multiple_bounds", bound=Union[Foo, Bar])

    assert FieldDefinition.from_annotation(str).bound_types is None
    assert FieldDefinition.from_annotation(T).bound_types is None

    bound_types = FieldDefinition.from_annotation(bound).bound_types

    assert bound_types
    assert len(bound_types) == 1
    assert isinstance(bound_types[0], FieldDefinition)
    assert bound_types[0].raw is Foo

    bound_types_union = FieldDefinition.from_annotation(multiple_bounds).bound_types
    assert bound_types_union
    assert len(bound_types_union) == 2
    assert bound_types_union[0].raw is Foo
    assert bound_types_union[1].raw is Bar


def test_nested_generic_types() -> None:
    V = TypeVar("V")

    class Foo(Generic[T]):
        pass

    class Bar(Generic[T, V]):
        pass

    class Baz(Generic[T], Bar[T, str]):
        pass

    fd_simple = FieldDefinition.from_annotation(Foo)
    assert fd_simple.generic_types
    assert len(fd_simple.generic_types) == 1
    assert fd_simple.generic_types[0].raw == T

    fd_union = FieldDefinition.from_annotation(Bar)
    assert fd_union.generic_types
    assert len(fd_union.generic_types) == 2
    assert fd_union.generic_types[0].raw == T
    assert fd_union.generic_types[1].raw == V

    fd_nested = FieldDefinition.from_annotation(Baz)
    assert fd_nested.generic_types
    assert len(fd_nested.generic_types) == 3
    assert fd_nested.generic_types[0].raw == T
    assert fd_nested.generic_types[1].raw == T
    assert fd_nested.generic_types[2].raw == str


@dataclass
class GenericDataclass(Generic[T]):
    foo: T


@dataclass
class NormalDataclass:
    foo: int


@pytest.mark.parametrize(
    ("annotation", "expected_type_hints"),
    ((GenericDataclass[str], {"foo": str}), (GenericDataclass, {"foo": T}), (NormalDataclass, {"foo": int})),
)
def test_field_definition_get_type_hints(annotation: Any, expected_type_hints: dict[str, Any]) -> None:
    assert (
        FieldDefinition.from_annotation(annotation).get_type_hints(include_extras=True, resolve_generics=True)
        == expected_type_hints
    )


@pytest.mark.parametrize(
    ("annotation", "expected_type_hints"),
    ((GenericDataclass[str], {"foo": T}), (GenericDataclass, {"foo": T}), (NormalDataclass, {"foo": int})),
)
def test_field_definition_get_type_hints_dont_resolve_generics(
    annotation: Any, expected_type_hints: dict[str, Any]
) -> None:
    assert (
        FieldDefinition.from_annotation(annotation).get_type_hints(include_extras=True, resolve_generics=False)
        == expected_type_hints
    )


@pytest.mark.parametrize(
    "predicate, expected_meta",
    [
        (annotated_types.LowerCase.__metadata__[0], {"lower_case": True}),  # pyright: ignore
        (annotated_types.UpperCase.__metadata__[0], {"upper_case": True}),  # pyright: ignore
        (annotated_types.IsAscii.__metadata__[0], {"pattern": "[[:ascii:]]"}),  # pyright: ignore
        (annotated_types.IsDigits.__metadata__[0], {"pattern": "[[:digit:]]"}),  # pyright: ignore
        (object(), {}),
    ],
)
def test_unpack_predicate(predicate: Any, expected_meta: dict[str, Any]) -> None:
    assert _unpack_predicate(predicate) == expected_meta


def test_warn_ambiguous_default_values() -> None:
    with pytest.warns(LitestarWarning, match="Ambiguous default values"):
        FieldDefinition.from_annotation(Annotated[int, Parameter(default=1)], default=2)


def test_warn_defaults_inside_parameter_definition() -> None:
    with pytest.warns(DeprecationWarning, match="Deprecated default value specification"):
        FieldDefinition.from_annotation(Annotated[int, Parameter(default=1)], default=1)
