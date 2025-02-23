import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum, auto
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Literal,
    Optional,
    TypedDict,
    TypeVar,
    Union,  # pyright: ignore
)

import annotated_types
import msgspec
import pytest
from msgspec import Struct
from typing_extensions import TypeAlias, TypeAliasType

from litestar import Controller, MediaType, get, post
from litestar._openapi.schema_generation.plugins import openapi_schema_plugins
from litestar._openapi.schema_generation.schema import (
    KWARG_DEFINITION_ATTRIBUTE_TO_OPENAPI_PROPERTY_MAP,
    SchemaCreator,
)
from litestar.app import DEFAULT_OPENAPI_CONFIG, Litestar
from litestar.di import Provide
from litestar.enums import ParamType
from litestar.exceptions import ImproperlyConfiguredException
from litestar.openapi.spec import ExternalDocumentation, OpenAPIType, Reference
from litestar.openapi.spec.example import Example
from litestar.openapi.spec.parameter import Parameter as OpenAPIParameter
from litestar.openapi.spec.schema import Schema
from litestar.pagination import ClassicPagination, CursorPagination, OffsetPagination
from litestar.params import KwargDefinition, Parameter, ParameterKwarg
from litestar.testing import create_test_client
from litestar.typing import FieldDefinition
from litestar.utils.helpers import get_name
from tests.helpers import get_schema_for_field_definition
from tests.models import DataclassPerson, DataclassPet

if TYPE_CHECKING:
    from types import ModuleType
    from typing import Callable

T = TypeVar("T")


def test_process_schema_result() -> None:
    test_str = "abc"
    kwarg_definition = ParameterKwarg(
        examples=[Example(value=1)],
        external_docs=ExternalDocumentation(url="https://example.com/docs"),
        content_encoding="utf-8",
        default=test_str,
        title=test_str,
        description=test_str,
        const=True,
        gt=1,
        ge=1,
        lt=1,
        le=1,
        multiple_of=1,
        min_items=1,
        max_items=1,
        min_length=1,
        max_length=1,
        pattern="^[a-z]$",
    )
    schema = get_schema_for_field_definition(
        FieldDefinition.from_annotation(annotation=str, kwarg_definition=kwarg_definition)
    )

    assert schema.title
    assert schema.const == test_str
    assert kwarg_definition.examples
    for signature_key, schema_key in KWARG_DEFINITION_ATTRIBUTE_TO_OPENAPI_PROPERTY_MAP.items():
        if schema_key == "examples":
            assert schema.examples == [kwarg_definition.examples[0].value]
        else:
            assert getattr(schema, schema_key) == getattr(kwarg_definition, signature_key)


def test_override_schema_component_key() -> None:
    @dataclass
    class Data:
        pass

    @post("/")
    def handler(
        data: Data,
    ) -> Annotated[Data, Parameter(schema_component_key="not_data")]:
        return Data()

    @get("/")
    def handler_2() -> Annotated[Data, Parameter(schema_component_key="not_data")]:
        return Data()

    app = Litestar([handler, handler_2])
    schema = app.openapi_schema.to_schema()
    # we expect the annotated / non-annotated to generate independent components
    assert schema["paths"]["/"]["post"]["requestBody"]["content"]["application/json"] == {
        "schema": {"$ref": "#/components/schemas/test_override_schema_component_key.Data"}
    }
    assert schema["paths"]["/"]["post"]["responses"]["201"]["content"] == {
        "application/json": {"schema": {"$ref": "#/components/schemas/not_data"}}
    }
    # a response with the same type and the same name should reference the same component
    assert schema["paths"]["/"]["get"]["responses"]["200"]["content"] == {
        "application/json": {"schema": {"$ref": "#/components/schemas/not_data"}}
    }
    assert app.openapi_schema.to_schema()["components"] == {
        "schemas": {
            "not_data": {"properties": {}, "type": "object", "required": [], "title": "Data"},
            "test_override_schema_component_key.Data": {
                "properties": {},
                "type": "object",
                "required": [],
                "title": "Data",
            },
        }
    }


def test_override_schema_component_key_raise_if_keys_are_not_unique() -> None:
    @dataclass
    class Data:
        pass

    @dataclass
    class Data2:
        pass

    @post("/")
    def handler(
        data: Data,
    ) -> Annotated[Data, Parameter(schema_component_key="not_data")]:
        return Data()

    @get("/")
    def handler_2() -> Annotated[Data2, Parameter(schema_component_key="not_data")]:
        return Data2()

    with pytest.raises(ImproperlyConfiguredException, match="Schema component keys must be unique"):
        Litestar([handler, handler_2]).openapi_schema.to_schema()


def test_dependency_schema_generation() -> None:
    async def top_dependency(query_param: int) -> int:
        return query_param

    async def mid_level_dependency(header_param: str = Parameter(header="header_param", required=False)) -> int:
        return 5

    async def local_dependency(path_param: int, mid_level: int, top_level: int) -> int:
        return path_param + mid_level + top_level

    class MyController(Controller):
        path = "/test"
        dependencies = {"mid_level": Provide(mid_level_dependency)}

        @get(
            path="/{path_param:int}",
            dependencies={
                "summed": Provide(local_dependency),
            },
            media_type=MediaType.TEXT,
        )
        def test_function(self, summed: int, handler_param: int) -> str:
            return str(summed)

    with create_test_client(
        MyController,
        dependencies={"top_level": Provide(top_dependency)},
        openapi_config=DEFAULT_OPENAPI_CONFIG,
    ) as client:
        handler = client.app.openapi_schema.paths["/test/{path_param}"]
        data = {param.name: {"in": param.param_in, "required": param.required} for param in handler.get.parameters}
        assert data == {
            "path_param": {"in": ParamType.PATH, "required": True},
            "header_param": {"in": ParamType.HEADER, "required": False},
            "query_param": {"in": ParamType.QUERY, "required": True},
            "handler_param": {"in": ParamType.QUERY, "required": True},
        }


def test_get_schema_for_annotation_enum() -> None:
    class Opts(str, Enum):
        opt1 = "opt1"
        opt2 = "opt2"

    schema = get_schema_for_field_definition(FieldDefinition.from_annotation(Opts))
    assert schema.enum == ["opt1", "opt2"]


ValueType: TypeAlias = Literal["a", "b", "c"]
ConstType: TypeAlias = Literal[1]


def test_handling_of_literals() -> None:
    @dataclass
    class DataclassWithLiteral:
        value: ValueType
        const: ConstType
        composite: Literal[ValueType, ConstType]

    schema = get_schema_for_field_definition(FieldDefinition.from_kwarg(name="", annotation=DataclassWithLiteral))

    assert isinstance(schema, Schema)
    assert schema.properties

    value = schema.properties["value"]
    assert isinstance(value, Schema)
    assert value.enum == ["a", "b", "c"]

    const = schema.properties["const"]
    assert isinstance(const, Schema)
    assert const.const == 1

    composite = schema.properties["composite"]
    assert isinstance(composite, Schema)
    assert composite.enum == ["a", "b", "c", 1]


def test_schema_hashing() -> None:
    schema = Schema(
        one_of=[
            Schema(type=OpenAPIType.STRING),
            Schema(type=OpenAPIType.NUMBER),
            Schema(type=OpenAPIType.OBJECT, properties={"key": Schema(type=OpenAPIType.STRING)}),
        ],
        examples=[None, [1, 2, 3]],
    )
    assert hash(schema)


def test_title_validation() -> None:
    # TODO: what is this actually testing?
    creator = SchemaCreator(plugins=openapi_schema_plugins)
    person_ref = creator.for_field_definition(FieldDefinition.from_kwarg(name="Person", annotation=DataclassPerson))
    pet_ref = creator.for_field_definition(FieldDefinition.from_kwarg(name="Pet", annotation=DataclassPet))
    assert isinstance(person_ref, Reference)
    assert isinstance(pet_ref, Reference)
    assert isinstance(creator.schema_registry.from_reference(person_ref).schema, Schema)
    assert isinstance(creator.schema_registry.from_reference(pet_ref).schema, Schema)


@pytest.mark.parametrize("with_future_annotations", [True, False])
def test_create_schema_for_dataclass_with_annotated_model_attribute(
    with_future_annotations: bool, create_module: "Callable[[str], ModuleType]"
) -> None:
    """Test that a model with an annotated attribute is correctly handled."""
    module = create_module(
        f"""
{'from __future__ import annotations' if with_future_annotations else ''}
from typing_extensions import Annotated
from dataclasses import dataclass

@dataclass
class Foo:
    foo: Annotated[int, "Foo description"]
"""
    )
    schema = get_schema_for_field_definition(FieldDefinition.from_annotation(module.Foo))
    assert schema.properties and "foo" in schema.properties


@pytest.mark.parametrize("with_future_annotations", [True, False])
def test_create_schema_for_typedict_with_annotated_required_and_not_required_model_attributes(
    with_future_annotations: bool, create_module: "Callable[[str], ModuleType]"
) -> None:
    """Test that a model with an annotated attribute is correctly handled."""
    module = create_module(
        f"""
{'from __future__ import annotations' if with_future_annotations else ''}
from typing_extensions import Annotated, Required, NotRequired
from typing import TypedDict

class Foo(TypedDict):
    foo: Annotated[int, "Foo description"]
    bar: Annotated[Required[int], "Bar description"]
    baz: Annotated[NotRequired[int], "Baz description"]
"""
    )
    schema = get_schema_for_field_definition(FieldDefinition.from_annotation(module.Foo))
    assert schema.properties and all(key in schema.properties for key in ("foo", "bar", "baz"))


def test_create_schema_from_msgspec_annotated_type() -> None:
    class Lookup(msgspec.Struct):
        str_field: Annotated[
            str,
            msgspec.Meta(max_length=16, examples=["example"], description="description", title="title", pattern=r"\w+"),
        ]
        bytes_field: Annotated[bytes, msgspec.Meta(max_length=2, min_length=1)]
        default_field: Annotated[str, msgspec.Meta(min_length=1)] = "a"

    schema = get_schema_for_field_definition(FieldDefinition.from_kwarg(name="Lookup", annotation=Lookup))

    assert schema.properties["str_field"].type == OpenAPIType.STRING  # type: ignore[index, union-attr]
    assert schema.properties["str_field"].examples == ["example"]  # type: ignore[index, union-attr]
    assert schema.properties["str_field"].description == "description"  # type: ignore[index]
    assert schema.properties["str_field"].title == "title"  # type: ignore[index, union-attr]
    assert schema.properties["str_field"].max_length == 16  # type: ignore[index, union-attr]
    assert sorted(schema.required) == sorted(["str_field", "bytes_field"])  # type: ignore[arg-type]
    assert schema.properties["bytes_field"].to_schema() == {  # type: ignore[index]
        "contentEncoding": "utf-8",
        "maxLength": 2,
        "minLength": 1,
        "type": "string",
    }


def test_annotated_types() -> None:
    historical_date = date(year=1980, day=1, month=1)
    today = date.today()

    @dataclass
    class MyDataclass:
        constrained_int: Annotated[int, annotated_types.Gt(1), annotated_types.Lt(10)]
        constrained_float: Annotated[float, annotated_types.Ge(1), annotated_types.Le(10)]
        constrained_date: Annotated[date, annotated_types.Interval(gt=historical_date, lt=today)]
        constrained_lower_case: annotated_types.LowerCase[str]
        constrained_upper_case: annotated_types.UpperCase[str]
        constrained_is_ascii: annotated_types.IsAscii[str]
        constrained_is_digit: annotated_types.IsDigit[str]

    schema = get_schema_for_field_definition(FieldDefinition.from_kwarg(name="MyDataclass", annotation=MyDataclass))

    assert schema.properties["constrained_int"].exclusive_minimum == 1  # type: ignore[index, union-attr]
    assert schema.properties["constrained_int"].exclusive_maximum == 10  # type: ignore[index, union-attr]
    assert schema.properties["constrained_float"].minimum == 1  # type: ignore[index, union-attr]
    assert schema.properties["constrained_float"].maximum == 10  # type: ignore[index, union-attr]
    assert datetime.fromtimestamp(
        schema.properties["constrained_date"].exclusive_minimum,  # type: ignore[arg-type, index, union-attr]
        tz=timezone.utc,
    ) == datetime.fromordinal(historical_date.toordinal()).replace(tzinfo=timezone.utc)
    assert datetime.fromtimestamp(
        schema.properties["constrained_date"].exclusive_maximum,  # type: ignore[arg-type, index, union-attr]
        tz=timezone.utc,
    ) == datetime.fromordinal(today.toordinal()).replace(tzinfo=timezone.utc)
    assert schema.properties["constrained_lower_case"].description == "must be in lower case"  # type: ignore[index]
    assert schema.properties["constrained_upper_case"].description == "must be in upper case"  # type: ignore[index]
    assert schema.properties["constrained_is_ascii"].pattern == "[[:ascii:]]"  # type: ignore[index, union-attr]
    assert schema.properties["constrained_is_digit"].pattern == "[[:digit:]]"  # type: ignore[index, union-attr]


def test_literal_enums() -> None:
    class Foo(Enum):
        A = auto()
        B = auto()

    schema = get_schema_for_field_definition(FieldDefinition.from_annotation(list[Literal[Foo.A]]))
    assert isinstance(schema.items, Schema)
    assert schema.items.const == 1


@dataclass
class DataclassGeneric(Generic[T]):
    foo: T
    optional_foo: Optional[T]
    annotated_foo: Annotated[T, object()]


class MsgspecGeneric(Struct, Generic[T]):
    foo: T
    optional_foo: Optional[T]
    annotated_foo: Annotated[T, object()]


annotations: list[type] = [DataclassGeneric[int], MsgspecGeneric[int]]

# Generic TypedDict was only supported from 3.11 onwards
if sys.version_info >= (3, 11):

    class TypedDictGeneric(TypedDict, Generic[T]):
        foo: T
        optional_foo: Optional[T]
        annotated_foo: Annotated[T, object()]

    annotations.append(TypedDictGeneric[int])


@pytest.mark.parametrize("cls", annotations)
def test_schema_generation_with_generic_classes(cls: Any) -> None:
    expected_foo_schema = Schema(type=OpenAPIType.INTEGER)
    expected_optional_foo_schema = Schema(one_of=[Schema(type=OpenAPIType.INTEGER), Schema(type=OpenAPIType.NULL)])

    properties = get_schema_for_field_definition(
        FieldDefinition.from_kwarg(name=get_name(cls), annotation=cls)
    ).properties
    assert properties
    assert properties["foo"] == expected_foo_schema
    assert properties["annotated_foo"] == expected_foo_schema
    assert properties["optional_foo"] == expected_optional_foo_schema


B = TypeVar("B", bound=int)
C = TypeVar("C", int, str)


@dataclass
class ConstrainedGenericDataclass(Generic[T, B, C]):
    bound: B
    constrained: C
    union: Union[T, bool]
    union_constrained: Union[C, bool]
    union_bound: Union[B, bool]


def test_schema_generation_with_generic_classes_constrained() -> None:
    cls = ConstrainedGenericDataclass
    properties = get_schema_for_field_definition(
        FieldDefinition.from_kwarg(name=cls.__name__, annotation=cls)
    ).properties

    assert properties
    assert properties["bound"] == Schema(type=OpenAPIType.INTEGER)
    assert properties["constrained"] == Schema(
        one_of=[Schema(type=OpenAPIType.INTEGER), Schema(type=OpenAPIType.STRING)]
    )
    assert properties["union"] == Schema(one_of=[Schema(type=OpenAPIType.OBJECT), Schema(type=OpenAPIType.BOOLEAN)])
    assert properties["union_constrained"] == Schema(
        one_of=[Schema(type=OpenAPIType.INTEGER), Schema(type=OpenAPIType.STRING), Schema(type=OpenAPIType.BOOLEAN)]
    )
    assert properties["union_bound"] == Schema(
        one_of=[Schema(type=OpenAPIType.INTEGER), Schema(type=OpenAPIType.BOOLEAN)]
    )


@pytest.mark.parametrize(
    "annotation",
    (
        ClassicPagination[DataclassGeneric[int]],
        OffsetPagination[DataclassGeneric[int]],
        CursorPagination[int, DataclassGeneric[int]],
    ),
)
def test_schema_generation_with_pagination(annotation: Any) -> None:
    expected_foo_schema = Schema(type=OpenAPIType.INTEGER)
    expected_optional_foo_schema = Schema(one_of=[Schema(type=OpenAPIType.INTEGER), Schema(type=OpenAPIType.NULL)])

    properties = get_schema_for_field_definition(FieldDefinition.from_annotation(annotation).inner_types[-1]).properties

    assert properties
    assert properties["foo"] == expected_foo_schema
    assert properties["annotated_foo"] == expected_foo_schema
    assert properties["optional_foo"] == expected_optional_foo_schema


def test_schema_generation_with_ellipsis() -> None:
    schema = get_schema_for_field_definition(FieldDefinition.from_annotation(tuple[int, ...]))
    assert isinstance(schema.items, Schema)
    assert schema.items.type == OpenAPIType.INTEGER


def test_schema_tuple_with_union() -> None:
    schema = get_schema_for_field_definition(FieldDefinition.from_annotation(tuple[int, Union[int, str]]))
    assert isinstance(schema.items, Schema)
    assert schema.items.one_of == [
        Schema(type=OpenAPIType.INTEGER),
        Schema(one_of=[Schema(type=OpenAPIType.INTEGER), Schema(type=OpenAPIType.STRING)]),
    ]


def test_optional_enum() -> None:
    class Foo(Enum):
        A = 1
        B = "b"

    creator = SchemaCreator(plugins=openapi_schema_plugins)
    schema = creator.for_field_definition(FieldDefinition.from_annotation(Optional[Foo]))
    assert isinstance(schema, Schema)
    assert schema.type is None
    assert schema.one_of is not None
    null_schema = schema.one_of[1]
    assert isinstance(null_schema, Schema)
    assert null_schema.type is not None
    assert null_schema.type is OpenAPIType.NULL
    enum_ref = schema.one_of[0]
    assert isinstance(enum_ref, Reference)
    assert enum_ref.ref == "#/components/schemas/tests_unit_test_openapi_test_schema_test_optional_enum.Foo"
    enum_schema = creator.schema_registry.from_reference(enum_ref).schema
    assert enum_schema.type
    assert set(enum_schema.type) == {OpenAPIType.INTEGER, OpenAPIType.STRING}
    assert enum_schema.enum
    assert enum_schema.enum[0] == 1
    assert enum_schema.enum[1] == "b"


def test_optional_str_specified_enum() -> None:
    class StringEnum(str, Enum):
        A = "a"
        B = "b"

    creator = SchemaCreator(plugins=openapi_schema_plugins)
    schema = creator.for_field_definition(FieldDefinition.from_annotation(Optional[StringEnum]))
    assert isinstance(schema, Schema)
    assert schema.type is None
    assert schema.one_of is not None

    enum_ref = schema.one_of[0]
    assert isinstance(enum_ref, Reference)
    assert (
        enum_ref.ref
        == "#/components/schemas/tests_unit_test_openapi_test_schema_test_optional_str_specified_enum.StringEnum"
    )
    enum_schema = creator.schema_registry.from_reference(enum_ref).schema
    assert enum_schema.type
    assert enum_schema.type == OpenAPIType.STRING
    assert enum_schema.enum
    assert enum_schema.enum[0] == "a"
    assert enum_schema.enum[1] == "b"

    null_schema = schema.one_of[1]
    assert isinstance(null_schema, Schema)
    assert null_schema.type is not None
    assert null_schema.type is OpenAPIType.NULL


def test_optional_int_specified_enum() -> None:
    class IntEnum(int, Enum):
        A = 1
        B = 2

    creator = SchemaCreator(plugins=openapi_schema_plugins)
    schema = creator.for_field_definition(FieldDefinition.from_annotation(Optional[IntEnum]))
    assert isinstance(schema, Schema)
    assert schema.type is None
    assert schema.one_of is not None

    enum_ref = schema.one_of[0]
    assert isinstance(enum_ref, Reference)
    assert (
        enum_ref.ref
        == "#/components/schemas/tests_unit_test_openapi_test_schema_test_optional_int_specified_enum.IntEnum"
    )
    enum_schema = creator.schema_registry.from_reference(enum_ref).schema
    assert enum_schema.type
    assert enum_schema.type == OpenAPIType.INTEGER
    assert enum_schema.enum
    assert enum_schema.enum[0] == 1
    assert enum_schema.enum[1] == 2

    null_schema = schema.one_of[1]
    assert isinstance(null_schema, Schema)
    assert null_schema.type is not None
    assert null_schema.type is OpenAPIType.NULL


def test_optional_literal() -> None:
    schema = get_schema_for_field_definition(FieldDefinition.from_annotation(Optional[Literal[1]]))
    assert schema.type is not None
    assert set(schema.type) == {OpenAPIType.INTEGER, OpenAPIType.NULL}
    assert schema.enum == [1, None]


def test_not_generating_examples_property() -> None:
    with_examples = SchemaCreator(generate_examples=True)
    without_examples = with_examples.not_generating_examples
    assert without_examples.generate_examples is False


def test_process_schema_result_with_unregistered_object_schema() -> None:
    """This test ensures that if a schema is created for an object and not registered in the schema registry, the
    schema is returned as-is, and not referenced.
    """
    schema = Schema(title="has title", type=OpenAPIType.OBJECT)
    field_definition = FieldDefinition.from_annotation(dict)
    assert SchemaCreator().process_schema_result(field_definition, schema) is schema


@pytest.mark.parametrize("base_type", [msgspec.Struct, TypedDict, dataclass])
def test_type_union(base_type: type) -> None:
    if base_type is dataclass:

        @dataclass
        class ModelA:  # pyright: ignore
            pass

        @dataclass
        class ModelB:  # pyright: ignore
            pass

    else:

        class ModelA(base_type):  # type: ignore[no-redef, misc]
            pass

        class ModelB(base_type):  # type: ignore[no-redef, misc]
            pass

    schema = get_schema_for_field_definition(
        FieldDefinition.from_kwarg(name="Lookup", annotation=Union[ModelA, ModelB])
    )
    assert schema.one_of == [
        Reference(ref="#/components/schemas/tests_unit_test_openapi_test_schema_test_type_union.ModelA"),
        Reference(ref="#/components/schemas/tests_unit_test_openapi_test_schema_test_type_union.ModelB"),
    ]


@pytest.mark.parametrize("base_type", [msgspec.Struct, TypedDict, dataclass])
def test_type_union_with_none(base_type: type) -> None:
    # https://github.com/litestar-org/litestar/issues/2971
    if base_type is dataclass:

        @dataclass
        class ModelA:  # pyright: ignore
            pass

        @dataclass
        class ModelB:  # pyright: ignore
            pass

    else:

        class ModelA(base_type):  # type: ignore[no-redef, misc]
            pass

        class ModelB(base_type):  # type: ignore[no-redef, misc]
            pass

    schema = get_schema_for_field_definition(
        FieldDefinition.from_kwarg(name="Lookup", annotation=Union[ModelA, ModelB, None])
    )
    assert schema.one_of == [
        Reference(ref="#/components/schemas/tests_unit_test_openapi_test_schema_test_type_union_with_none.ModelA"),
        Reference("#/components/schemas/tests_unit_test_openapi_test_schema_test_type_union_with_none.ModelB"),
        Schema(type=OpenAPIType.NULL),
    ]


def test_default_only_on_field_definition() -> None:
    field_definition = FieldDefinition.from_annotation(int, default=10)
    assert field_definition.kwarg_definition is None

    schema = get_schema_for_field_definition(field_definition)
    assert schema.default == 10


def test_default_not_provided_for_kwarg_but_for_field() -> None:
    field_definition = FieldDefinition.from_annotation(int, default=10, kwarg_definition=KwargDefinition())
    schema = get_schema_for_field_definition(field_definition)

    assert schema.default == 10


def test_routes_with_different_path_param_types_get_merged() -> None:
    # https://github.com/litestar-org/litestar/issues/2700
    @get("/{param:int}")
    async def get_handler(param: int) -> None:
        pass

    @post("/{param:str}")
    async def post_handler(param: str) -> None:
        pass

    app = Litestar([get_handler, post_handler])
    assert app.openapi_schema.paths
    paths = app.openapi_schema.paths["/{param}"]
    assert paths.get is not None
    assert paths.post is not None


def test_unconsumed_path_parameters_are_documented() -> None:
    # https://github.com/litestar-org/litestar/issues/3290
    # https://github.com/litestar-org/litestar/issues/3369

    async def dd(param3: Annotated[str, Parameter(description="123")]) -> str:
        return param3

    async def d(dep_dep: str, param2: Annotated[str, Parameter(description="abc")]) -> str:
        return f"{dep_dep}_{param2}"

    @get("/{param1:str}/{param2:str}/{param3:str}", dependencies={"dep": d, "dep_dep": dd})
    async def handler(dep: str) -> None:
        pass

    app = Litestar([handler])
    params = app.openapi_schema.paths["/{param1}/{param2}/{param3}"].get.parameters  # type: ignore[index, union-attr]
    assert params
    assert len(params) == 3
    for i, param in enumerate(sorted(params, key=lambda p: p.name), 1):  # pyright: ignore
        assert isinstance(param, OpenAPIParameter)
        assert param.name == f"param{i}"
        assert param.required is True
        assert param.param_in is ParamType.PATH


def test_type_alias_type() -> None:
    @get("/")
    def handler(query_param: Annotated[TypeAliasType("IntAlias", int), Parameter(description="foo")]) -> None:  # type: ignore[valid-type]
        pass

    app = Litestar([handler])
    param = app.openapi_schema.paths["/"].get.parameters[0]  # type: ignore[index, union-attr]
    assert param.schema.type is OpenAPIType.INTEGER  # type: ignore[union-attr]
    # ensure other attributes than the plain type are carried over correctly
    assert param.description == "foo"


@pytest.mark.skipif(sys.version_info < (3, 12), reason="type keyword not available before 3.12")
def test_type_alias_type_keyword() -> None:
    ctx: dict[str, Any] = {}
    exec("type IntAlias = int", ctx, None)
    annotation = ctx["IntAlias"]

    @get("/")
    def handler(query_param: Annotated[annotation, Parameter(description="foo")]) -> None:  # type: ignore[valid-type]
        pass

    app = Litestar([handler])
    param = app.openapi_schema.paths["/"].get.parameters[0]  # type: ignore[union-attr, index]
    assert param.schema.type is OpenAPIType.INTEGER  # type: ignore[union-attr]
    # ensure other attributes than the plain type are carried over correctly
    assert param.description == "foo"
