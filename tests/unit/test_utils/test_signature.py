# ruff: noqa: UP006,UP007

from __future__ import annotations

import inspect
import warnings
from inspect import Parameter
from types import ModuleType
from typing import Annotated, Any, Callable, Generic, Optional, TypeVar, Union, get_type_hints

import pytest
from typing_extensions import NotRequired, Required, TypedDict, get_args

from litestar import Controller, post
from litestar.exceptions import ImproperlyConfiguredException
from litestar.exceptions.base_exceptions import LitestarWarning
from litestar.response.base import ASGIResponse
from litestar.types.asgi_types import Receive, Scope, Send
from litestar.types.builtin_types import NoneType
from litestar.types.empty import Empty
from litestar.typing import FieldDefinition
from litestar.utils.signature import ParsedSignature, add_types_to_signature_namespace, get_fn_type_hints

T = TypeVar("T")
U = TypeVar("U")


class ConcreteT: ...


def test_get_fn_type_hints_asgi_app() -> None:
    app = ASGIResponse()
    assert get_fn_type_hints(app.__call__) == {"scope": Scope, "receive": Receive, "send": Send, "return": NoneType}


def func(a: int, b: str, c: float) -> None: ...


class C:
    def __init__(self, a: int, b: str, c: float) -> None: ...

    def method(self, a: int, b: str, c: float) -> None: ...

    def __call__(self, a: int, b: str, c: float) -> None: ...


@pytest.mark.parametrize("fn", [func, C, C(1, "2", 3.0).method, C(1, "2", 3.0)])
def test_get_fn_type_hints(fn: Any) -> None:
    assert get_fn_type_hints(fn) == {"a": int, "b": str, "c": float, "return": NoneType}


def test_get_fn_type_hints_class_no_init() -> None:
    """Test that get_fn_type_hints works with classes that don't have an __init__ method.

    Ref: https://github.com/litestar-org/litestar/issues/1504
    """

    class C: ...

    assert get_fn_type_hints(C) == {}


@pytest.mark.parametrize(
    ("hint",),
    [
        ("Optional[str]",),
        ("Union[str, None]",),
        ("Union[str, int, None]",),
        ("Optional[Union[str, int]]",),
        ("Union[str, int]",),
        ("str",),
    ],
)
def test_get_fn_type_hints_with_none_default(hint: str, create_module: Callable[[str], ModuleType]) -> None:
    mod = create_module(
        f"""
from typing import *
from typing_extensions import Annotated

def fn(plain: {hint} = None, annotated: Annotated[{hint}, ...] = None) -> None: ...
    """
    )
    hints = get_fn_type_hints(mod.fn)
    assert hints["plain"] == get_args(hints["annotated"])[0]


class _TD(TypedDict):
    req_int: Required[int]
    req_list_int: Required[list[int]]
    not_req_int: NotRequired[int]
    not_req_list_int: NotRequired[list[int]]
    ann_req_int: Required[Annotated[int, "foo"]]
    ann_req_list_int: Required[Annotated[list[int], "foo"]]


test_type_hints = get_type_hints(_TD, include_extras=True)
field_definition_int = FieldDefinition.from_annotation(int)


def _check_field_definition(field_definition: FieldDefinition, expected: dict[str, Any]) -> None:
    for key, value in expected.items():
        assert getattr(field_definition, key) == value


def test_field_definition_from_parameter() -> None:
    """Test FieldDefinition."""
    param = Parameter("foo", Parameter.POSITIONAL_OR_KEYWORD, annotation=int)
    parsed_param = FieldDefinition.from_parameter(param, {"foo": int})
    assert parsed_param.name == "foo"
    assert parsed_param.default is Empty
    assert parsed_param.annotation is int


def test_field_definition_from_parameter_raises_improperly_configured_if_no_annotation() -> None:
    """Test FieldDefinition raises ImproperlyConfigured if no annotation."""
    param = Parameter("foo", Parameter.POSITIONAL_OR_KEYWORD)
    with pytest.raises(ImproperlyConfiguredException):
        FieldDefinition.from_parameter(param, {})


def test_field_definition_from_parameter_has_default_predicate() -> None:
    """Test FieldDefinition.has_default."""
    param = Parameter("foo", Parameter.POSITIONAL_OR_KEYWORD, annotation=int)
    parsed_param = FieldDefinition.from_parameter(param, {"foo": int})
    assert parsed_param.has_default is False

    param = Parameter("foo", Parameter.POSITIONAL_OR_KEYWORD, annotation=int, default=42)
    parsed_param = FieldDefinition.from_parameter(param, {"foo": int})
    assert parsed_param.has_default is True


def test_field_definition_from_parameter_annotation_property() -> None:
    """Test FieldDefinition.annotation."""
    param = Parameter("foo", Parameter.POSITIONAL_OR_KEYWORD, annotation=int)
    parsed_param = FieldDefinition.from_parameter(param, {"foo": int})
    assert parsed_param.annotation is int
    assert parsed_param.annotation is int


def test_parsed_signature() -> None:
    """Test ParsedSignature."""

    def fn(foo: int, bar: Optional[list[int]] = None) -> None: ...

    parsed_sig = ParsedSignature.from_fn(fn, get_fn_type_hints(fn))
    assert parsed_sig.return_type.annotation is NoneType
    assert parsed_sig.parameters["foo"].annotation is int
    assert parsed_sig.parameters["bar"].args == (list[int], NoneType)
    assert parsed_sig.parameters["bar"].annotation == Union[list[int], NoneType]
    assert parsed_sig.parameters["bar"].default is None
    assert parsed_sig.original_signature == inspect.signature(fn)


def test_add_types_to_signature_namespace() -> None:
    """Test add_types_to_signature_namespace."""
    ns = add_types_to_signature_namespace([int, str], {})
    assert ns == {"int": int, "str": str}


def test_add_types_to_signature_namespace_no_warn(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test add_types_to_signature_namespace with existing types."""
    monkeypatch.delenv("LITESTAR_WARN_SIGNATURE_NAMESPACE_OVERRIDE", raising=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        add_types_to_signature_namespace([int], {"int": int})


def test_add_types_to_signature_namespace_with_existing_types_warn(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test add_types_to_signature_namespace with existing types raises."""
    monkeypatch.delenv("LITESTAR_WARN_SIGNATURE_NAMESPACE_OVERRIDE", raising=False)
    with pytest.warns(LitestarWarning):
        add_types_to_signature_namespace([int], {"int": str})


def test_add_types_to_signature_namespace_warn_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test add_types_to_signature_namespace with existing types."""
    monkeypatch.setenv("LITESTAR_WARN_SIGNATURE_NAMESPACE_OVERRIDE", "0")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        add_types_to_signature_namespace([int], {"int": str})


@pytest.mark.parametrize(
    ("namespace", "expected"),
    (
        ({T: int}, {"data": int, "return": int}),
        ({}, {"data": T, "return": T}),
        ({T: ConcreteT}, {"data": ConcreteT, "return": ConcreteT}),
    ),
)
def test_using_generics_in_fn_annotations(namespace: dict[str, Any], expected: dict[str, Any]) -> None:
    @post(signature_namespace=namespace)
    def create_item(data: T) -> T:
        return data

    signature = create_item.parsed_fn_signature
    actual = {"data": signature.parameters["data"].annotation, "return": signature.return_type.annotation}
    assert actual == expected


class GenericController(Controller, Generic[T]):
    model_class: T

    def __class_getitem__(cls, model_class: type) -> type:
        cls_dict = {"model_class": model_class}
        return type(f"GenericController[{model_class.__name__}", (cls,), cls_dict)

    def __init__(self) -> None:
        super().__init__()
        self.signature_namespace[T] = self.model_class  # type: ignore[misc]


class BaseController(GenericController[T]):
    @post()
    async def create(self, data: T) -> T:
        return data


@pytest.mark.parametrize(
    ("annotation_type", "expected"),
    (
        (int, {"data": int, "return": int}),
        (float, {"data": float, "return": float}),
        (ConcreteT, {"data": ConcreteT, "return": ConcreteT}),
    ),
)
def test_using_generics_in_controller_annotations(annotation_type: type, expected: dict[str, Any]) -> None:
    class ConcreteController(BaseController[annotation_type]):  # type: ignore[valid-type]
        path = "/"

    controller_object = ConcreteController()

    signature = (controller_object.get_route_handlers()[0]).merge(controller_object.as_router()).parsed_fn_signature
    actual = {"data": signature.parameters["data"].annotation, "return": signature.return_type.annotation}
    assert actual == expected
