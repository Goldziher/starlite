from __future__ import annotations

import dataclasses
from dataclasses import replace
from typing import TYPE_CHECKING, Annotated, Any, Generic, TypeVar
from warnings import warn

from typing_extensions import TypeAlias, override

from litestar.dto.base_dto import AbstractDTO
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.dto.field import DTO_FIELD_META_KEY, extract_dto_field
from litestar.exceptions import MissingDependencyException, ValidationException
from litestar.plugins.pydantic.utils import get_model_info, is_pydantic_2_model, is_pydantic_undefined, is_pydantic_v2
from litestar.types.empty import Empty
from litestar.typing import FieldDefinition

if TYPE_CHECKING:
    from collections.abc import Collection, Generator

    from litestar.dto import DTOConfig

try:
    import pydantic as _  # noqa: F401
except ImportError as e:
    raise MissingDependencyException("pydantic") from e


try:
    import pydantic as pydantic_v2

    if not is_pydantic_v2(pydantic_v2):
        raise ImportError

    from pydantic import ValidationError as ValidationErrorV2
    from pydantic import v1 as pydantic_v1
    from pydantic.v1 import ValidationError as ValidationErrorV1

    ModelType: TypeAlias = "pydantic_v1.BaseModel | pydantic_v2.BaseModel"  # pyright: ignore[reportInvalidTypeForm,reportGeneralTypeIssues]

except ImportError:
    import pydantic as pydantic_v1  # type: ignore[no-redef]

    pydantic_v2 = Empty  # type: ignore[assignment]
    from pydantic import ValidationError as ValidationErrorV1  # type: ignore[assignment]

    ValidationErrorV2 = ValidationErrorV1  # type: ignore[assignment, misc]
    ModelType = "pydantic_v1.BaseModel"  # type: ignore[misc]


T = TypeVar("T", bound="ModelType | Collection[ModelType]")


__all__ = ("PydanticDTO",)

_down_types: dict[Any, Any] = {
    pydantic_v1.EmailStr: str,
    pydantic_v1.IPvAnyAddress: str,
    pydantic_v1.IPvAnyInterface: str,
    pydantic_v1.IPvAnyNetwork: str,
}

if pydantic_v2 is not Empty:  # type: ignore[comparison-overlap]  # pragma: no cover
    _down_types.update(
        {
            pydantic_v2.JsonValue: Any,
            pydantic_v2.EmailStr: str,
            pydantic_v2.IPvAnyAddress: str,
            pydantic_v2.IPvAnyInterface: str,
            pydantic_v2.IPvAnyNetwork: str,
        }
    )


def convert_validation_error(validation_error: ValidationErrorV1 | ValidationErrorV2) -> list[dict[str, Any]]:  # pyright: ignore[reportInvalidTypeForm,reportGeneralTypeIssues]
    error_list = validation_error.errors()
    for error in error_list:
        if isinstance(exception := error.get("ctx", {}).get("error"), Exception):
            error["ctx"]["error"] = type(exception).__name__  # pyright: ignore[reportTypedDictNotRequiredAccess]
    return error_list  # type: ignore[return-value]


def downtype_for_data_transfer(field_definition: FieldDefinition) -> FieldDefinition:
    if sub := _down_types.get(field_definition.annotation):
        return FieldDefinition.from_kwarg(
            annotation=Annotated[sub, field_definition.metadata], name=field_definition.name
        )
    return field_definition


class PydanticDTO(AbstractDTO[T], Generic[T]):
    """Support for domain modelling with Pydantic."""

    @override
    def decode_builtins(self, value: dict[str, Any]) -> Any:
        try:
            return super().decode_builtins(value)
        except (ValidationErrorV2, ValidationErrorV1) as ex:
            raise ValidationException(extra=convert_validation_error(ex)) from ex

    @override
    def decode_bytes(self, value: bytes) -> Any:
        try:
            return super().decode_bytes(value)
        except (ValidationErrorV2, ValidationErrorV1) as ex:
            raise ValidationException(extra=convert_validation_error(ex)) from ex

    @classmethod
    def generate_field_definitions(
        cls,
        model_type: type[pydantic_v1.BaseModel | pydantic_v2.BaseModel],  # pyright: ignore[reportInvalidTypeForm,reportGeneralTypeIssues]
    ) -> Generator[DTOFieldDefinition, None, None]:
        model_info = get_model_info(model_type)
        model_fields = model_info.model_fields
        model_field_definitions = model_info.field_definitions

        for field_name, field_definition in model_field_definitions.items():
            field_definition = downtype_for_data_transfer(field_definition)
            dto_field = extract_dto_field(field_definition, field_definition.extra)

            default: Any = Empty
            default_factory: Any = None
            if field_info := model_fields.get(field_name):
                # field_info might not exist, since FieldInfo isn't provided by pydantic
                # for computed fields, but we still generate a FieldDefinition for them
                try:
                    extra = field_info.extra  # type: ignore[union-attr]
                except AttributeError:
                    extra = field_info.json_schema_extra  # type: ignore[union-attr]

                if extra is not None and extra.pop(DTO_FIELD_META_KEY, None):
                    warn(
                        message="Declaring 'DTOField' via Pydantic's 'Field.extra' is deprecated. "
                        "Use 'Annotated', e.g., 'Annotated[str, DTOField(mark='read-only')]' instead. "
                        "Support for 'DTOField' in 'Field.extra' will be removed in v3.",
                        category=DeprecationWarning,
                        stacklevel=2,
                    )

                if not is_pydantic_undefined(field_info.default):
                    default = field_info.default
                elif field_definition.is_optional:
                    default = None
                else:
                    default = Empty

                default_factory = (
                    field_info.default_factory
                    if field_info.default_factory and not is_pydantic_undefined(field_info.default_factory)
                    else None
                )

            yield replace(
                DTOFieldDefinition.from_field_definition(
                    field_definition=field_definition,
                    dto_field=dto_field,
                    model_name=model_type.__name__,
                    default_factory=default_factory,
                    # we don't want the constraints to be set on the DTO struct as
                    # constraints, but as schema metadata only, so we can let pydantic
                    # handle all the constraining
                    passthrough_constraints=False,
                ),
                default=default,
                name=field_name,
            )

    @classmethod
    def detect_nested_field(cls, field_definition: FieldDefinition) -> bool:
        if pydantic_v2 is not Empty:  # type: ignore[comparison-overlap]
            return field_definition.is_subclass_of((pydantic_v1.BaseModel, pydantic_v2.BaseModel))
        return field_definition.is_subclass_of(pydantic_v1.BaseModel)  # type: ignore[unreachable]

    @classmethod
    def get_config_for_model_type(cls, config: DTOConfig, model_type: type[Any]) -> DTOConfig:
        if is_pydantic_2_model(model_type) and (model_config := getattr(model_type, "model_config", None)):
            if model_config.get("extra") == "forbid":
                config = dataclasses.replace(config, forbid_unknown_fields=True)
        elif issubclass(model_type, pydantic_v1.BaseModel) and (model_config := getattr(model_type, "Config", None)):  # noqa: SIM102
            if getattr(model_config, "extra", None) == "forbid":
                config = dataclasses.replace(config, forbid_unknown_fields=True)
        return config
