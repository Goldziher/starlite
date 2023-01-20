from datetime import datetime
from decimal import Decimal
from enum import Enum, EnumMeta
from re import Pattern
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Type, Union

from pydantic import (
    BaseModel,
    ConstrainedBytes,
    ConstrainedDate,
    ConstrainedDecimal,
    ConstrainedFloat,
    ConstrainedFrozenSet,
    ConstrainedInt,
    ConstrainedList,
    ConstrainedSet,
    ConstrainedStr,
)
from pydantic_factories import ModelFactory
from pydantic_factories.exceptions import ParameterError
from pydantic_factories.utils import is_pydantic_model
from pydantic_openapi_schema.utils.utils import OpenAPI310PydanticSchema
from pydantic_openapi_schema.v3_1_0.example import Example
from pydantic_openapi_schema.v3_1_0.schema import Schema

from starlite.datastructures.pagination import (
    ClassicPagination,
    CursorPagination,
    OffsetPagination,
)
from starlite.datastructures.upload_file import UploadFile
from starlite.exceptions import ImproperlyConfiguredException
from starlite.openapi.constants import (
    EXTRA_TO_OPENAPI_PROPERTY_MAP,
    KWARG_MODEL_ATTRIBUTE_TO_OPENAPI_PROPERTY_MAP,
    TYPE_MAP,
)
from starlite.openapi.enums import OpenAPIFormat, OpenAPIType
from starlite.openapi.utils import get_openapi_type_for_complex_type
from starlite.signature.models import SignatureField
from starlite.types import Empty
from starlite.utils import is_dataclass_class_or_instance, is_typed_dict
from starlite.utils.model import convert_dataclass_to_model, convert_typeddict_to_model

if TYPE_CHECKING:
    from starlite.plugins.base import PluginProtocol


def normalize_example_value(value: Any) -> Any:
    """Normalize the example value to make it look a bit prettier."""
    if isinstance(value, (Decimal, float)):
        value = round(float(value), 2)
    if isinstance(value, Enum):
        value = value.value
    if is_dataclass_class_or_instance(value):
        value = convert_dataclass_to_model(value)
    if isinstance(value, BaseModel):
        value = value.dict()
    if isinstance(value, (list, set)):
        value = [normalize_example_value(v) for v in value]
    if isinstance(value, dict):
        for k, v in value.items():
            value[k] = normalize_example_value(v)
    return value


class ExampleFactory(ModelFactory[BaseModel]):
    """A factory that always returns values."""

    __model__ = BaseModel
    __allow_none_optionals__ = False


def create_numerical_constrained_field_schema(
    field_type: Union[Type["ConstrainedFloat"], Type["ConstrainedInt"], Type["ConstrainedDecimal"]]
) -> Schema:
    """Create Schema from Constrained Int/Float/Decimal field."""
    schema = Schema(type=OpenAPIType.INTEGER if issubclass(field_type, int) else OpenAPIType.NUMBER)
    if field_type.le is not None:
        schema.maximum = float(field_type.le)
    if field_type.lt is not None:
        schema.exclusiveMaximum = float(field_type.lt)
    if field_type.ge is not None:
        schema.minimum = float(field_type.ge)
    if field_type.gt is not None:
        schema.exclusiveMinimum = float(field_type.gt)
    if field_type.multiple_of is not None:
        schema.multipleOf = float(field_type.multiple_of)
    return schema


def create_date_constrained_field_schema(field_type: Type["ConstrainedDate"]) -> Schema:
    """Create Schema from Constrained Date Field."""
    schema = Schema(type=OpenAPIType.STRING, schema_format=OpenAPIFormat.DATE)
    if field_type.le is not None:
        schema.maximum = float(datetime.combine(field_type.le, datetime.min.time()).timestamp())
    if field_type.lt is not None:
        schema.exclusiveMaximum = float(datetime.combine(field_type.lt, datetime.min.time()).timestamp())
    if field_type.ge is not None:
        schema.minimum = float(datetime.combine(field_type.ge, datetime.min.time()).timestamp())
    if field_type.gt is not None:
        schema.exclusiveMinimum = float(datetime.combine(field_type.gt, datetime.min.time()).timestamp())
    return schema


def create_string_constrained_field_schema(
    field_type: Union[Type["ConstrainedStr"], Type["ConstrainedBytes"]]
) -> Schema:
    """Create Schema from Constrained Str/Bytes field."""
    schema = Schema(type=OpenAPIType.STRING)
    if field_type.min_length:
        schema.minLength = field_type.min_length
    if field_type.max_length:
        schema.maxLength = field_type.max_length
    if issubclass(field_type, ConstrainedStr) and isinstance(field_type.regex, Pattern):
        schema.pattern = field_type.regex.pattern
    if field_type.to_lower:
        schema.description = "must be in lower case"
    return schema


def create_collection_constrained_field_schema(
    field_type: Union[Type[ConstrainedList], Type["ConstrainedSet"], Type["ConstrainedFrozenSet"]],
    children: Optional[Tuple["SignatureField", ...]],
    plugins: List["PluginProtocol"],
) -> Schema:
    """Create Schema from Constrained List/Set field."""
    schema = Schema(type=OpenAPIType.ARRAY)
    if field_type.min_items:
        schema.minItems = field_type.min_items
    if field_type.max_items:
        schema.maxItems = field_type.max_items
    if issubclass(field_type, (ConstrainedSet, ConstrainedFrozenSet)):
        schema.uniqueItems = True
    if children:
        items = [create_schema(field=sub_field, generate_examples=False, plugins=plugins) for sub_field in children]
        if len(items) > 1:
            schema.items = Schema(oneOf=items)  # type: ignore[arg-type]
        else:
            schema.items = items[0]
    else:
        schema.items = create_schema(
            field=SignatureField.create(field_type=field_type.item_type, name=f"{field_type.__name__}Field"),
            generate_examples=False,
            plugins=plugins,
        )
    return schema


def create_constrained_field_schema(
    field_type: Union[
        Type["ConstrainedBytes"],
        Type["ConstrainedDate"],
        Type["ConstrainedDecimal"],
        Type["ConstrainedFloat"],
        Type["ConstrainedFrozenSet"],
        Type["ConstrainedInt"],
        Type["ConstrainedList"],
        Type["ConstrainedSet"],
        Type["ConstrainedStr"],
    ],
    children: Optional[List["SignatureField"]],
    plugins: List["PluginProtocol"],
) -> "Schema":
    """Create Schema for Pydantic Constrained fields (created using constr(), conint() and so forth, or by subclassing
    Constrained*)
    """
    if issubclass(field_type, (ConstrainedFloat, ConstrainedInt, ConstrainedDecimal)):
        return create_numerical_constrained_field_schema(field_type=field_type)
    if issubclass(field_type, (ConstrainedStr, ConstrainedBytes)):
        return create_string_constrained_field_schema(field_type=field_type)
    if issubclass(field_type, ConstrainedDate):
        return create_date_constrained_field_schema(field_type=field_type)
    return create_collection_constrained_field_schema(field_type=field_type, children=tuple(children) if children else None, plugins=plugins)


def update_schema_with_signature_field(schema: "Schema", signature_field: "SignatureField") -> "Schema":
    """Copy values from the given instance of pydantic FieldInfo into the schema."""
    if (
        signature_field.kwarg_model
        and signature_field.is_const
        and signature_field.default_value not in {None, ..., Empty}
        and schema.const is None
    ):
        schema.const = signature_field.default_value
    for kwarg_model_key, schema_key in KWARG_MODEL_ATTRIBUTE_TO_OPENAPI_PROPERTY_MAP.items():
        value = getattr(signature_field.kwarg_model, kwarg_model_key)
        if value not in {None, ..., Empty}:
            setattr(schema, schema_key, value)
    for extra_key, schema_key in EXTRA_TO_OPENAPI_PROPERTY_MAP.items():
        if extra_key in signature_field.extra:
            value = signature_field.extra[extra_key]
            if value not in (None, ..., Empty):
                setattr(schema, schema_key, value)
    return schema


class GenericPydanticSchema(OpenAPI310PydanticSchema):
    """Special `Schema` class to indicate a reference from pydantic 'GenericClass' instances."""

    schema_class: Any


def get_schema_for_field_type(field: "SignatureField", plugins: List["PluginProtocol"]) -> "Schema":
    """Get or create a Schema object for the given field type."""
    field_type = field.field_type
    if field_type in TYPE_MAP:
        return TYPE_MAP[field_type].copy()
    if is_pydantic_model(field_type):
        return OpenAPI310PydanticSchema(schema_class=field_type)
    if is_dataclass_class_or_instance(field_type):
        return OpenAPI310PydanticSchema(schema_class=convert_dataclass_to_model(field_type))
    if is_typed_dict(field_type):
        return OpenAPI310PydanticSchema(schema_class=convert_typeddict_to_model(field_type))
    if isinstance(field_type, (EnumMeta, Enum)):
        enum_values: List[Union[str, int]] = [v.value for v in field_type]  # type: ignore
        openapi_type = OpenAPIType.STRING if isinstance(enum_values[0], str) else OpenAPIType.INTEGER
        return Schema(type=openapi_type, enum=enum_values)
    if any(plugin.is_plugin_supported_type(field_type) for plugin in plugins):
        plugin = [plugin for plugin in plugins if plugin.is_plugin_supported_type(field_type)][0]
        return OpenAPI310PydanticSchema(
            schema_class=plugin.to_pydantic_model_class(field_type, parameter_name=field.name)
        )
    if field_type is UploadFile:
        # the following is a hack -https://www.openapis.org/blog/2021/02/16/migrating-from-openapi-3-0-to-3-1-0
        # the format for OA 3.1 is type + contentMediaType, for 3.0.* is type + format, we do both.
        return Schema(  # type: ignore
            type=OpenAPIType.STRING,
            format="binary",
            contentMediaType="application/octet-stream",
        )
    # this is a failsafe to ensure we always return a value
    return Schema()  # pragma: no cover


def get_schema_for_generic_type(field: "SignatureField", plugins: List["PluginProtocol"]) -> "Schema":
    """Handle generic types.

    Raises:
        ImproperlyConfiguredException: if generic type is not supported.

    Args:
        field: Pydantic '"SignatureField"' instance.
        plugins: A list of plugins.

    Returns:
        A schema.
    """
    field_type = field.field_type

    if field_type is ClassicPagination:
        return Schema(
            type=OpenAPIType.OBJECT,
            properties={
                "items": Schema(
                    type=OpenAPIType.ARRAY,
                    items=create_schema(
                        field=field.children[0],  # type: ignore[index]
                        generate_examples=False,
                        plugins=plugins,
                    ),
                ),
                "page_size": Schema(type=OpenAPIType.INTEGER, description="Number of items per page."),
                "current_page": Schema(type=OpenAPIType.INTEGER, description="Current page number."),
                "total_pages": Schema(type=OpenAPIType.INTEGER, description="Total number of pages."),
            },
        )

    if field_type is OffsetPagination:
        return Schema(
            type=OpenAPIType.OBJECT,
            properties={
                "items": Schema(
                    type=OpenAPIType.ARRAY,
                    items=create_schema(
                        field=field.children[0],  # type: ignore[index]
                        generate_examples=False,
                        plugins=plugins,
                    ),
                ),
                "limit": Schema(type=OpenAPIType.INTEGER, description="Maximal number of items to send."),
                "offset": Schema(type=OpenAPIType.INTEGER, description="Offset from the beginning of the query."),
                "total": Schema(type=OpenAPIType.INTEGER, description="Total number of items."),
            },
        )

    if field_type is CursorPagination:
        cursor_schema = create_schema(field=field.children[0], generate_examples=False, plugins=plugins)  # type: ignore[index]
        cursor_schema.description = "Unique ID, designating the last identifier in the given data set. This value can be used to request the 'next' batch of records."

        return Schema(
            type=OpenAPIType.OBJECT,
            properties={
                "items": Schema(
                    type=OpenAPIType.ARRAY,
                    items=create_schema(
                        field=field.children[1],  # type: ignore[index]
                        generate_examples=False,
                        plugins=plugins,
                    ),
                ),
                "cursor": cursor_schema,
                "results_per_page": Schema(type=OpenAPIType.INTEGER, description="Maximal number of items to send."),
            },
        )
    raise ImproperlyConfiguredException(f"cannot generate OpenAPI schema for generic type {field_type}")


def create_examples_for_field(field: "SignatureField") -> List["Example"]:
    """Use the pydantic-factories package to create an example value for the given schema."""
    try:
        value = normalize_example_value(ExampleFactory.get_field_value(field))
        return [Example(description=f"Example {field.name} value", value=value)]
    except ParameterError:  # pragma: no cover
        return []


def create_schema(
    field: "SignatureField", generate_examples: bool, plugins: List["PluginProtocol"], ignore_optional: bool = False
) -> "Schema":
    """Create a Schema model for a given SignatureField and if needed - recursively traverse its children as well."""

    if field.is_optional and not ignore_optional:
        non_optional_schema = create_schema(
            field=field,
            generate_examples=False,
            ignore_optional=True,
            plugins=plugins,
        )
        schema = Schema(
            oneOf=[
                Schema(type=OpenAPIType.NULL),
                *(non_optional_schema.oneOf or [non_optional_schema]),
            ]
        )
    elif field.is_union:
        schema = Schema(
            oneOf=[
                create_schema(field=sub_field, generate_examples=False, plugins=plugins)
                for sub_field in field.children or []
            ]
        )
    elif ModelFactory.is_constrained_field(field.field_type):
        # constrained fields are those created using the pydantic functions constr, conint, conlist etc.
        # or subclasses of the Constrained* pydantic classes by other means
        schema = create_constrained_field_schema(
            field_type=field.field_type, children=list(field.children or ()), plugins=plugins
        )
    elif field.children and not field.is_generic:
        openapi_type = get_openapi_type_for_complex_type(field)
        schema = Schema(type=openapi_type)
        if openapi_type == OpenAPIType.ARRAY:
            items = [
                create_schema(
                    field=sub_field,
                    generate_examples=False,
                    plugins=plugins,
                )
                for sub_field in field.children
            ]
            if len(items) > 1:
                schema.items = Schema(oneOf=items)  # type: ignore[arg-type] # pragma: no cover
            else:
                schema.items = items[0]
    elif field.is_generic:
        schema = get_schema_for_generic_type(field=field, plugins=plugins)
    else:
        # value is not a complex typing - hence we can try and get the value schema directly
        schema = get_schema_for_field_type(field=field, plugins=plugins)
    if not ignore_optional:
        schema = update_schema_with_signature_field(schema=schema, signature_field=field)
    if not schema.examples and generate_examples:
        schema.examples = create_examples_for_field(field=field)
    return schema
