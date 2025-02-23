# mypy: strict-equality=False
# pyright: reportGeneralTypeIssues=false
from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from inspect import isclass
from typing import TYPE_CHECKING, Annotated, Any, Callable, Literal, Optional, get_type_hints

from litestar.openapi.spec import Example
from litestar.params import KwargDefinition, ParameterKwarg
from litestar.types import Empty
from litestar.typing import FieldDefinition
from litestar.utils import deprecated, is_class_and_subclass, is_generic, is_undefined_sentinel
from litestar.utils.typing import (
    _substitute_typevars,
    get_origin_or_inner_type,
    get_safe_generic_origin,
    get_type_hints_with_generics_resolved,
    normalize_type_annotation,
)

# isort: off
try:
    from pydantic import v1 as pydantic_v1
    import pydantic as pydantic_v2
    from pydantic.fields import PydanticUndefined as Pydantic2Undefined  # type: ignore[attr-defined]
    from pydantic.v1.fields import Undefined as Pydantic1Undefined

    PYDANTIC_UNDEFINED_SENTINELS = {Pydantic1Undefined, Pydantic2Undefined}
except ImportError:
    try:
        import pydantic as pydantic_v1  # type: ignore[no-redef]
        from pydantic.fields import Undefined as Pydantic1Undefined  # type: ignore[attr-defined, no-redef]

        pydantic_v2 = Empty  # type: ignore[assignment]
        PYDANTIC_UNDEFINED_SENTINELS = {Pydantic1Undefined}

    except ImportError:  # pyright: ignore
        pydantic_v1 = Empty  # type: ignore[assignment]
        pydantic_v2 = Empty  # type: ignore[assignment]
        PYDANTIC_UNDEFINED_SENTINELS = set()
# isort: on


if TYPE_CHECKING:
    from types import ModuleType

    from typing_extensions import TypeGuard


def is_pydantic_model_class(
    annotation: Any,
) -> TypeGuard[type[pydantic_v1.BaseModel | pydantic_v2.BaseModel]]:  # pyright: ignore
    """Given a type annotation determine if the annotation is a subclass of pydantic's BaseModel.

    Args:
        annotation: A type.

    Returns:
        A typeguard determining whether the type is :data:`BaseModel pydantic.BaseModel>`.
    """
    tests: list[bool] = []

    if pydantic_v1 is not Empty:  # pragma: no cover
        tests.append(is_class_and_subclass(annotation, pydantic_v1.BaseModel))

    if pydantic_v2 is not Empty:  # pragma: no cover
        tests.append(is_class_and_subclass(annotation, pydantic_v2.BaseModel))

    return any(tests)


def is_pydantic_model_instance(
    annotation: Any,
) -> TypeGuard[pydantic_v1.BaseModel | pydantic_v2.BaseModel]:  # pyright: ignore
    """Given a type annotation determine if the annotation is an instance of pydantic's BaseModel.

    Args:
        annotation: A type.

    Returns:
        A typeguard determining whether the type is :data:`BaseModel pydantic.BaseModel>`.
    """
    tests: list[bool] = []

    if pydantic_v1 is not Empty:  # pragma: no cover
        tests.append(isinstance(annotation, pydantic_v1.BaseModel))

    if pydantic_v2 is not Empty:  # pragma: no cover
        tests.append(isinstance(annotation, pydantic_v2.BaseModel))

    return any(tests)


def is_pydantic_constrained_field(annotation: Any) -> bool:
    """Check if the given annotation is a constrained pydantic type.

    Args:
        annotation: A type annotation

    Returns:
        True if pydantic is installed and the type is a constrained type, otherwise False.
    """
    if pydantic_v1 is Empty:  # pragma: no cover
        return False  # type: ignore[unreachable]

    return any(
        is_class_and_subclass(annotation, constrained_type)  # pyright: ignore
        for constrained_type in (
            pydantic_v1.ConstrainedBytes,
            pydantic_v1.ConstrainedDate,
            pydantic_v1.ConstrainedDecimal,
            pydantic_v1.ConstrainedFloat,
            pydantic_v1.ConstrainedFrozenSet,
            pydantic_v1.ConstrainedInt,
            pydantic_v1.ConstrainedList,
            pydantic_v1.ConstrainedSet,
            pydantic_v1.ConstrainedStr,
        )
    )


def pydantic_unwrap_and_get_origin(annotation: Any) -> Any | None:
    if pydantic_v2 is Empty or (pydantic_v1 is not Empty and is_class_and_subclass(annotation, pydantic_v1.BaseModel)):
        return get_origin_or_inner_type(annotation)

    origin = annotation.__pydantic_generic_metadata__["origin"]
    return normalize_type_annotation(origin)


def pydantic_get_type_hints_with_generics_resolved(
    annotation: Any,
    globalns: dict[str, Any] | None = None,
    localns: dict[str, Any] | None = None,
    include_extras: bool = False,
    model_annotations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if pydantic_v2 is Empty or (pydantic_v1 is not Empty and is_class_and_subclass(annotation, pydantic_v1.BaseModel)):
        return get_type_hints_with_generics_resolved(annotation, type_hints=model_annotations)

    origin = pydantic_unwrap_and_get_origin(annotation)
    if origin is None:
        if model_annotations is None:  # pragma: no cover
            model_annotations = get_type_hints(
                annotation, globalns=globalns, localns=localns, include_extras=include_extras
            )
        typevar_map = {p: p for p in annotation.__pydantic_generic_metadata__["parameters"]}
    else:
        if model_annotations is None:
            model_annotations = get_type_hints(
                origin, globalns=globalns, localns=localns, include_extras=include_extras
            )
        args = annotation.__pydantic_generic_metadata__["args"]
        parameters = origin.__pydantic_generic_metadata__["parameters"]
        typevar_map = dict(zip(parameters, args))

    return {n: _substitute_typevars(type_, typevar_map) for n, type_ in model_annotations.items()}


@deprecated(version="2.6.2")
def pydantic_get_unwrapped_annotation_and_type_hints(annotation: Any) -> tuple[Any, dict[str, Any]]:  # pragma: no cover
    """Get the unwrapped annotation and the type hints after resolving generics.

    Args:
        annotation: A type annotation.

    Returns:
        A tuple containing the unwrapped annotation and the type hints.
    """

    if is_generic(annotation):
        origin = pydantic_unwrap_and_get_origin(annotation)
        return origin or annotation, pydantic_get_type_hints_with_generics_resolved(annotation, include_extras=True)
    return annotation, get_type_hints(annotation, include_extras=True)


def is_pydantic_2_model(
    obj: type[pydantic_v1.BaseModel | pydantic_v2.BaseModel],  # pyright: ignore
) -> TypeGuard[pydantic_v2.BaseModel]:  # pyright: ignore
    return pydantic_v2 is not Empty and issubclass(obj, pydantic_v2.BaseModel)


def is_pydantic_undefined(value: Any) -> bool:
    return any(v is value for v in PYDANTIC_UNDEFINED_SENTINELS)


def create_field_definitions_for_computed_fields(
    model: type[pydantic_v1.BaseModel | pydantic_v2.BaseModel],  # pyright: ignore
    prefer_alias: bool,
) -> dict[str, FieldDefinition]:
    """Create field definitions for computed fields.

    Args:
        model: A pydantic model.
        prefer_alias: Whether to prefer the alias or the name of the field.

    Returns:
        A dictionary containing the field definitions for the computed fields.
    """
    pydantic_decorators = getattr(model, "__pydantic_decorators__", None)
    if pydantic_decorators is None:
        return {}

    def get_name(k: str, dec: Any) -> str:
        if not dec.info.alias:
            return k
        return dec.info.alias if prefer_alias else k  # type: ignore[no-any-return]

    return {
        (name := get_name(k, dec)): FieldDefinition.from_annotation(
            Annotated[
                dec.info.return_type,
                KwargDefinition(
                    title=dec.info.title,
                    description=dec.info.description,
                    read_only=True,
                    examples=[Example(value=v) for v in examples] if (examples := dec.info.examples) else None,
                    schema_extra=dec.info.json_schema_extra,
                ),
            ],
            name=name,
        )
        for k, dec in pydantic_decorators.computed_fields.items()
    }


def is_pydantic_v2(module: ModuleType) -> bool:
    """Determine if the given module is pydantic v2.

    Given a module we expect to be a pydantic version, determine if it is pydantic v2.

    Args:
        module: A module.

    Returns:
        True if the module is pydantic v2, otherwise False.
    """
    return bool(module.__version__.startswith("2."))


@dataclass(frozen=True)
class PydanticModelInfo:
    pydantic_version: Literal["1", "2"]
    field_definitions: dict[str, FieldDefinition]
    model_fields: dict[str, pydantic_v1.fields.FieldInfo | pydantic_v2.fields.FieldInfo]  # pyright: ignore[reportInvalidTypeForm,reportGeneralTypeIssues]
    title: str | None = None
    example: Any | None = None
    is_generic: bool = False


_CreateFieldDefinition = Callable[..., FieldDefinition]


def _create_field_definition_v1(  # noqa: C901
    field_annotation: Any,
    *,
    field_info: pydantic_v1.fields.FieldInfo,  # pyright: ignore[reportInvalidTypeForm,reportGeneralTypeIssues]
    **field_definition_kwargs: Any,
) -> FieldDefinition:
    kwargs: dict[str, Any] = {}
    examples: list[Any] = []
    if example := field_info.extra.get("example"):
        examples.append(example)
    if extra_examples := field_info.extra.get("examples"):
        examples.extend(extra_examples)
    if examples:
        kwargs["examples"] = [Example(value=e) for e in examples]
    if title := field_info.title:
        kwargs["title"] = title
    if description := field_info.description:
        kwargs["description"] = description

    kwarg_definition: KwargDefinition | None = None

    if isclass(field_annotation):
        if issubclass(field_annotation, pydantic_v1.ConstrainedBytes):  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue]
            kwarg_definition = ParameterKwarg(
                min_length=field_annotation.min_length,
                max_length=field_annotation.max_length,
                lower_case=field_annotation.to_lower,
                upper_case=field_annotation.to_upper,
                **kwargs,
            )
            field_definition_kwargs["raw"] = field_annotation
            field_annotation = bytes
        elif issubclass(field_annotation, pydantic_v1.ConstrainedStr):  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue]
            kwarg_definition = ParameterKwarg(
                min_length=field_annotation.min_length,
                max_length=field_annotation.max_length,
                lower_case=field_annotation.to_lower,
                upper_case=field_annotation.to_upper,
                pattern=field_annotation.regex.pattern
                if isinstance(field_annotation.regex, re.Pattern)
                else field_annotation.regex,
                **kwargs,
            )
            field_definition_kwargs["raw"] = field_annotation
            field_annotation = str
        elif issubclass(field_annotation, pydantic_v1.ConstrainedDate):  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue]
            # TODO: The typings of ParameterKwarg need fixing. Specifically, the
            # gt/ge/lt/le fields need to be typed with protocols, such that they may
            # accept any type that implements the respective comparisons

            kwarg_definition = ParameterKwarg(
                gt=field_annotation.gt,  # type: ignore[arg-type]
                ge=field_annotation.ge,  # type: ignore[arg-type]
                lt=field_annotation.lt,  # type: ignore[arg-type]
                le=field_annotation.le,  # type: ignore[arg-type]
                **kwargs,
            )
            field_definition_kwargs["raw"] = field_annotation
            field_annotation = datetime.date
        elif issubclass(
            field_annotation,
            (pydantic_v1.ConstrainedInt, pydantic_v1.ConstrainedFloat, pydantic_v1.ConstrainedDecimal),  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue]
        ):
            kwarg_definition = ParameterKwarg(
                gt=field_annotation.gt,  # type: ignore[arg-type]
                ge=field_annotation.ge,  # type: ignore[arg-type]
                lt=field_annotation.lt,  # type: ignore[arg-type]
                le=field_annotation.le,  # type: ignore[arg-type]
                multiple_of=field_annotation.multiple_of,  # type: ignore[arg-type]
                **kwargs,
            )
            field_definition_kwargs["raw"] = field_annotation
            field_annotation = field_annotation.mro()[2]
        elif issubclass(
            field_annotation,
            (pydantic_v1.ConstrainedList, pydantic_v1.ConstrainedSet, pydantic_v1.ConstrainedFrozenSet),  # pyright: ignore[reportArgumentType,reportAttributeAccessIssue]
        ):
            kwarg_definition = ParameterKwarg(
                max_items=field_annotation.max_items, min_items=field_annotation.min_items, **kwargs
            )
            field_definition_kwargs["raw"] = field_annotation
            # on < 3.9, these builtins are not generic
            origin = get_safe_generic_origin(field_annotation.__origin__, field_annotation.__origin__)
            field_annotation = origin[field_annotation.item_type]

    if kwarg_definition is None and kwargs:
        kwarg_definition = ParameterKwarg(**kwargs)

    if kwarg_definition:
        field_definition_kwargs["raw"] = field_annotation
        field_annotation = Annotated[field_annotation, kwarg_definition]

    return FieldDefinition.from_annotation(
        annotation=field_annotation,
        **field_definition_kwargs,
    )


def _create_field_definition_v2(  # noqa: C901
    field_annotation: Any,
    *,
    field_info: pydantic_v2.fields.FieldInfo,  # pyright: ignore[reportInvalidTypeForm,reportGeneralTypeIssues]
    **field_definition_kwargs: Any,
) -> FieldDefinition:
    kwargs: dict[str, Any] = {}
    examples: list[Any] = []
    field_meta: list[Any] = []

    if json_schema_extra := field_info.json_schema_extra:
        if callable(json_schema_extra):
            raise ValueError("Callables not supported for json_schema_extra")
        if json_schema_example := json_schema_extra.get("example"):
            del json_schema_extra["example"]
            examples.append(json_schema_example)
        if json_schema_examples := json_schema_extra.get("examples"):
            del json_schema_extra["examples"]
            examples.extend(json_schema_examples)  # type: ignore[arg-type]
    if field_examples := field_info.examples:
        examples.extend(field_examples)

    if examples:
        if not json_schema_extra:
            json_schema_extra = {}
        json_schema_extra["examples"] = examples

    if description := field_info.description:
        kwargs["description"] = description

    if title := field_info.title:
        kwargs["title"] = title

    for meta in field_info.metadata:
        if isinstance(meta, pydantic_v2.types.StringConstraints):  # pyright: ignore[reportAttributeAccessIssue]
            kwargs["min_length"] = meta.min_length
            kwargs["max_length"] = meta.max_length
            kwargs["pattern"] = meta.pattern
            kwargs["lower_case"] = meta.to_lower
            kwargs["upper_case"] = meta.to_upper
        # forward other metadata
        else:
            field_meta.append(meta)

    if json_schema_extra:
        kwargs["schema_extra"] = json_schema_extra

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if kwargs:
        kwarg_definition = ParameterKwarg(**kwargs)
        field_meta.append(kwarg_definition)

    if field_meta:
        field_definition_kwargs["raw"] = field_annotation
        for meta in field_meta:
            field_annotation = Annotated[field_annotation, meta]

    return FieldDefinition.from_annotation(
        annotation=field_annotation,
        **field_definition_kwargs,
    )


def get_model_info(
    annotation: Any,
    prefer_alias: bool = False,
) -> PydanticModelInfo:
    model: type[pydantic_v1.BaseModel | pydantic_v2.BaseModel]  # pyright: ignore[reportInvalidTypeForm,reportGeneralTypeIssues]

    if is_generic(annotation):
        is_generic_model = True
        model = pydantic_unwrap_and_get_origin(annotation) or annotation
    else:
        is_generic_model = False
        model = annotation

    if is_pydantic_2_model(model):
        model_config = model.model_config
        model_field_info = model.model_fields
        title = model_config.get("title")
        example = model_config.get("example")
        is_v2_model = True
    else:
        model_config = model.__config__  # type: ignore[assignment, union-attr]
        model_field_info = model.__fields__  # type: ignore[assignment]
        title = getattr(model_config, "title", None)
        example = getattr(model_config, "example", None)
        is_v2_model = False

    model_fields: dict[str, pydantic_v1.fields.FieldInfo | pydantic_v2.fields.FieldInfo] = {  # pyright: ignore[reportInvalidTypeForm,reportGeneralTypeIssues]
        k: getattr(f, "field_info", f) for k, f in model_field_info.items()
    }

    if is_v2_model:
        # extract the annotations from the FieldInfo. This allows us to skip fields
        # which have been marked as private
        # if there's a default factory, we wrap the field in 'Optional', to signal
        # that it is not required
        model_annotations = {
            k: Optional[field_info.annotation] if field_info.default_factory else field_info.annotation  # type: ignore[union-attr]
            for k, field_info in model_fields.items()
        }

    else:
        # pydantic v1 requires some workarounds here
        model_annotations = {
            k: f.outer_type_ if f.required or f.default else Optional[f.outer_type_]
            for k, f in model.__fields__.items()  # type: ignore[union-attr]
        }

    if is_generic_model:
        # if the model is generic, resolve the type variables. We pass in the
        # already extracted annotations, to keep the logic of respecting private
        # fields consistent with the above
        model_annotations = pydantic_get_type_hints_with_generics_resolved(
            annotation, model_annotations=model_annotations, include_extras=True
        )

    create_field_definition: _CreateFieldDefinition = (
        _create_field_definition_v2 if is_v2_model else _create_field_definition_v1  # type: ignore[assignment]
    )

    property_fields = {
        field_info.alias if field_info.alias and prefer_alias else k: create_field_definition(
            field_annotation=model_annotations[k],
            name=field_info.alias if field_info.alias and prefer_alias else k,
            default=Empty
            if is_undefined_sentinel(field_info.default) or is_pydantic_undefined(field_info.default)
            else field_info.default,
            field_info=field_info,
        )
        for k, field_info in model_fields.items()
    }

    computed_field_definitions = create_field_definitions_for_computed_fields(
        model,
        prefer_alias=prefer_alias,
    )
    property_fields.update(computed_field_definitions)

    return PydanticModelInfo(
        pydantic_version="2" if is_v2_model else "1",
        title=title,
        example=example,
        field_definitions=property_fields,
        is_generic=is_generic_model,
        model_fields=model_fields,
    )
