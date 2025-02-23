from typing import Generic, Optional, TypeVar

from litestar.dto import DataclassDTO
from litestar.typing import FieldDefinition
from tests.models import DataclassPerson

T = TypeVar("T")


def test_resolve_model_type_optional() -> None:
    field_definition = FieldDefinition.from_annotation(Optional[int])
    assert DataclassDTO[DataclassPerson].resolve_model_type(field_definition) == FieldDefinition.from_annotation(int)


def test_resolve_generic_wrapper_type_no_origin() -> None:
    field_definition = FieldDefinition.from_annotation(int)
    assert DataclassDTO[DataclassPerson].resolve_generic_wrapper_type(field_definition) is None


def test_resolve_generic_wrapper_type_origin_no_parameters() -> None:
    field_definition = FieldDefinition.from_annotation(list[int])
    assert DataclassDTO[DataclassPerson].resolve_generic_wrapper_type(field_definition) is None


def test_resolve_generic_wrapper_type_model_type_not_subtype_of_specialized_type() -> None:
    class Wrapper(Generic[T]):
        t: T

    field_definition = FieldDefinition.from_annotation(Wrapper[int])

    assert DataclassDTO[DataclassPerson].resolve_generic_wrapper_type(field_definition) is None


def test_resolve_generic_wrapper_type_type_var_not_attribute() -> None:
    class Wrapper(Generic[T]):
        def returns_t(self) -> T:  # type:ignore[empty-body]
            ...

    field_definition = FieldDefinition.from_annotation(Wrapper[int])

    assert DataclassDTO[DataclassPerson].resolve_generic_wrapper_type(field_definition) is None
