from typing import Annotated, Any
from unittest.mock import ANY

import pydantic as pydantic_v2
import pytest
from pydantic import v1 as pydantic_v1

from litestar import get, post
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.plugins.pydantic import PydanticDTO, PydanticInitPlugin, PydanticPlugin
from litestar.status_codes import HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client
from tests.unit.test_plugins.test_pydantic.models import PydanticPerson, PydanticV1Person

from . import BaseModelType, PydanticVersion


@pytest.mark.parametrize(("meta",), [(None,), (Body(media_type=RequestEncodingType.URL_ENCODED),)])
def test_pydantic_v1_validation_error_raises_400(meta: Any) -> None:
    class Model(pydantic_v1.BaseModel):
        foo: str = pydantic_v1.Field(max_length=2)

    ModelDTO = PydanticDTO[Model]

    annotation: Any
    annotation = Annotated[Model, meta] if meta is not None else Model

    @post(dto=ModelDTO, signature_namespace={"annotation": annotation})
    def handler(data: annotation) -> Any:  # pyright: ignore
        return data

    model_json = {"foo": "too long"}
    expected_errors: list[dict[str, Any]]

    expected_errors = [
        {
            "loc": ["foo"],
            "msg": "ensure this value has at most 2 characters",
            "type": "value_error.any_str.max_length",
            "ctx": {"limit_value": 2},
        }
    ]

    with create_test_client(route_handlers=handler) as client:
        kws = {"data": model_json} if meta else {"json": model_json}
        response = client.post("/", **kws)  # type: ignore[arg-type]
        extra = response.json()["extra"]

        assert response.status_code == 400
        assert extra == expected_errors


@pytest.mark.parametrize(("meta",), [(None,), (Body(media_type=RequestEncodingType.URL_ENCODED),)])
def test_pydantic_v2_validation_error_raises_400(meta: Any) -> None:
    class Model(pydantic_v2.BaseModel):
        foo: str = pydantic_v2.Field(max_length=2)

    ModelDTO = PydanticDTO[Model]

    annotation: Any
    annotation = Annotated[Model, meta] if meta is not None else Model

    @post(dto=ModelDTO, signature_namespace={"annotation": annotation})
    def handler(data: annotation) -> Any:  # pyright: ignore
        return data

    model_json = {"foo": "too long"}
    expected_errors: list[dict[str, Any]]

    expected_errors = [
        {
            "type": "string_too_long",
            "loc": ["foo"],
            "msg": "String should have at most 2 characters",
            "input": "too long",
            "ctx": {"max_length": 2},
        }
    ]

    with create_test_client(route_handlers=handler) as client:
        kws = {"data": model_json} if meta else {"json": model_json}
        response = client.post("/", **kws)  # type: ignore[arg-type]

        extra = response.json()["extra"]
        extra[0].pop("url")

        assert response.status_code == 400
        assert extra == expected_errors


def test_default_error_handling() -> None:
    @post("/{param:int}")
    def my_route_handler(param: int, data: PydanticPerson) -> None: ...

    with create_test_client(my_route_handler) as client:
        response = client.post("/123", json={"first_name": "moishe"})
        extra = response.json().get("extra")
        assert extra is not None
        assert len(extra) == 5


def test_default_error_handling_v1() -> None:
    @post("/{param:int}")
    def my_route_handler(param: int, data: PydanticV1Person) -> None: ...

    with create_test_client(my_route_handler) as client:
        response = client.post("/123", json={"first_name": "moishe"})
        extra = response.json().get("extra")
        assert extra is not None
        assert len(extra) == 4


def test_serialize_raw_errors_v2() -> None:
    # https://github.com/litestar-org/litestar/issues/2365
    class User(pydantic_v2.BaseModel):
        user_id: int

        @pydantic_v2.field_validator("user_id")
        @classmethod
        def validate_user_id(cls, user_id: int) -> None:
            raise ValueError("user id must be greater than 0")

    @post("/", dto=PydanticDTO[User])
    async def create_user(data: User) -> User:
        return data

    with create_test_client(create_user) as client:
        response = client.post("/", json={"user_id": -1})
        extra = response.json().get("extra")
        assert extra == [
            {
                "type": "value_error",
                "loc": ["user_id"],
                "msg": "Value error, user id must be greater than 0",
                "input": -1,
                "ctx": {"error": "ValueError"},
                "url": ANY,
            }
        ]


def test_signature_model_invalid_input(base_model: BaseModelType, pydantic_version: PydanticVersion) -> None:
    class OtherChild(base_model):  # type: ignore[misc, valid-type]
        val: list[int]

    class Child(base_model):  # type: ignore[misc, valid-type]
        val: int
        other_val: int

    class Parent(base_model):  # type: ignore[misc, valid-type]
        child: Child
        other_child: OtherChild

    @post("/")
    def test(
        data: Parent,
        int_param: int,
        length_param: str = Parameter(min_length=2),
        int_header: int = Parameter(header="X-SOME-INT"),
        int_cookie: int = Parameter(cookie="int-cookie"),
    ) -> None: ...

    with create_test_client(route_handlers=[test], signature_types=[Parent]) as client:
        client.cookies.update({"int-cookie": "cookie"})
        response = client.post(
            "/",
            json={"child": {"val": "a", "other_val": "b"}, "other_child": {"val": [1, "c"]}},
            params={"int_param": "param", "length_param": "d"},
            headers={"X-SOME-INT": "header"},
        )

        assert response.status_code == HTTP_400_BAD_REQUEST

        data = response.json()

        assert data
        if pydantic_version == "v1":
            assert data["extra"] == [
                {"key": "child.val", "message": "value is not a valid integer"},
                {"key": "child.other_val", "message": "value is not a valid integer"},
                {"key": "other_child.val.1", "message": "value is not a valid integer"},
            ]
        else:
            assert data["extra"] == [
                {
                    "message": "Input should be a valid integer, unable to parse string as an integer",
                    "key": "child.val",
                },
                {
                    "message": "Input should be a valid integer, unable to parse string as an integer",
                    "key": "child.other_val",
                },
                {
                    "message": "Input should be a valid integer, unable to parse string as an integer",
                    "key": "other_child.val.1",
                },
            ]


class V1ModelWithPrivateFields(pydantic_v1.BaseModel):
    class Config:
        underscore_fields_are_private = True

    _field: str = pydantic_v1.PrivateAttr()
    # include an invalid annotation here to ensure we never touch those fields
    _underscore_field: "foo"  # type: ignore[name-defined] # noqa: F821
    bar: str


class V2ModelWithPrivateFields(pydantic_v2.BaseModel):
    class Config:
        underscore_fields_are_private = True

    _field: str = pydantic_v2.PrivateAttr()
    bar: str


@pytest.mark.parametrize("model_type", [V1ModelWithPrivateFields, V2ModelWithPrivateFields])
def test_private_fields(model_type: BaseModelType) -> None:
    @post("/")
    async def handler(data: V2ModelWithPrivateFields) -> V2ModelWithPrivateFields:
        return data

    with create_test_client([handler]) as client:
        res = client.post("/", json={"bar": "value"})
        assert res.status_code == 201
        assert res.json() == {"bar": "value"}


@pytest.mark.parametrize(
    ("base_model", "type_", "in_"),
    [
        pytest.param(pydantic_v2.BaseModel, pydantic_v2.JsonValue, {"foo": "bar"}, id="pydantic_v2.JsonValue"),
        pytest.param(
            pydantic_v1.BaseModel, pydantic_v1.IPvAnyAddress, "127.0.0.1", id="pydantic_v1.IPvAnyAddress (v4)"
        ),
        pytest.param(
            pydantic_v2.BaseModel, pydantic_v2.IPvAnyAddress, "127.0.0.1", id="pydantic_v2.IPvAnyAddress (v4)"
        ),
        pytest.param(
            pydantic_v1.BaseModel,
            pydantic_v1.IPvAnyAddress,
            "2001:db8::ff00:42:8329",
            id="pydantic_v1.IPvAnyAddress (v6)",
        ),
        pytest.param(
            pydantic_v2.BaseModel,
            pydantic_v2.IPvAnyAddress,
            "2001:db8::ff00:42:8329",
            id="pydantic_v2.IPvAnyAddress (v6)",
        ),
        pytest.param(
            pydantic_v1.BaseModel, pydantic_v1.IPvAnyInterface, "127.0.0.1/24", id="pydantic_v1.IPvAnyInterface (v4)"
        ),
        pytest.param(
            pydantic_v2.BaseModel, pydantic_v2.IPvAnyInterface, "127.0.0.1/24", id="pydantic_v2.IPvAnyInterface (v4)"
        ),
        pytest.param(
            pydantic_v1.BaseModel,
            pydantic_v1.IPvAnyInterface,
            "2001:db8::ff00:42:8329/128",
            id="pydantic_v1.IPvAnyInterface (v6)",
        ),
        pytest.param(
            pydantic_v2.BaseModel,
            pydantic_v2.IPvAnyInterface,
            "2001:db8::ff00:42:8329/128",
            id="pydantic_v2.IPvAnyInterface (v6)",
        ),
        pytest.param(
            pydantic_v1.BaseModel, pydantic_v1.IPvAnyNetwork, "127.0.0.1/32", id="pydantic_v1.IPvAnyNetwork (v4)"
        ),
        pytest.param(
            pydantic_v2.BaseModel, pydantic_v2.IPvAnyNetwork, "127.0.0.1/32", id="pydantic_v2.IPvAnyNetwork (v4)"
        ),
        pytest.param(
            pydantic_v1.BaseModel,
            pydantic_v1.IPvAnyNetwork,
            "2001:db8::ff00:42:8329/128",
            id="pydantic_v1.IPvAnyNetwork (v6)",
        ),
        pytest.param(
            pydantic_v2.BaseModel,
            pydantic_v2.IPvAnyNetwork,
            "2001:db8::ff00:42:8329/128",
            id="pydantic_v2.IPvAnyNetwork (v6)",
        ),
        pytest.param(pydantic_v1.BaseModel, pydantic_v1.EmailStr, "test@example.com", id="pydantic_v1.EmailStr"),
        pytest.param(pydantic_v2.BaseModel, pydantic_v2.EmailStr, "test@example.com", id="pydantic_v2.EmailStr"),
    ],
)
def test_dto_with_non_instantiable_types(base_model: BaseModelType, type_: Any, in_: Any) -> None:
    class Model(base_model):  # type: ignore[misc, valid-type]
        foo: type_

    @post("/", dto=PydanticDTO[Model])
    async def handler(data: Model) -> Model:
        return data

    with create_test_client(handler) as client:
        res = client.post("/", json={"foo": in_})
        assert res.status_code == 201
        assert res.json() == {"foo": in_}


@pytest.mark.parametrize(
    "plugin_params, response",
    (
        (
            {"exclude": {"alias"}},
            {
                "none": None,
                "default": "default",
            },
        ),
        ({"exclude_defaults": True}, {"alias": "prefer_alias"}),
        ({"exclude_none": True}, {"alias": "prefer_alias", "default": "default"}),
        ({"exclude_unset": True}, {"alias": "prefer_alias"}),
        ({"include": {"alias"}}, {"alias": "prefer_alias"}),
        ({"prefer_alias": True}, {"prefer_alias": "prefer_alias", "default": "default", "none": None}),
    ),
    ids=(
        "Exclude alias field",
        "Exclude default fields",
        "Exclude None field",
        "Exclude unset fields",
        "Include alias field",
        "Use alias in response",
    ),
)
def test_params_with_v1_and_v2_models(plugin_params: dict, response: dict) -> None:
    class ModelV1(pydantic_v1.BaseModel):  # pyright: ignore
        alias: str = pydantic_v1.fields.Field(alias="prefer_alias")  # pyright: ignore
        default: str = "default"
        none: None = None

        class Config:
            allow_population_by_field_name = True

    class ModelV2(pydantic_v2.BaseModel):
        alias: str = pydantic_v2.fields.Field(serialization_alias="prefer_alias")
        default: str = "default"
        none: None = None

    @post("/v1")
    async def handler_v1() -> ModelV1:
        return ModelV1(alias="prefer_alias")  # type: ignore[call-arg]

    @post("/v2")
    async def handler_v2() -> ModelV2:
        return ModelV2(alias="prefer_alias")

    with create_test_client([handler_v1, handler_v2], plugins=[PydanticPlugin(**plugin_params)]) as client:
        assert client.post("/v1").json() == response
        assert client.post("/v2").json() == response


@pytest.mark.parametrize(
    "validate_strict,expect_error",
    [
        (False, False),
        (None, False),
        (True, True),
    ],
)
def test_v2_strict_validate(
    validate_strict: bool,
    expect_error: bool,
) -> None:
    # https://github.com/litestar-org/litestar/issues/3572

    class Model(pydantic_v2.BaseModel):
        test_bool: pydantic_v2.StrictBool

    @post("/")
    async def handler(data: Model) -> None:
        return None

    plugins = []
    if validate_strict is not None:
        plugins.append(PydanticInitPlugin(validate_strict=validate_strict))

    with create_test_client([handler], plugins=plugins) as client:
        res = client.post("/", json={"test_bool": "YES"})
        assert res.status_code == 400 if expect_error else 201


def test_model_defaults(pydantic_version: PydanticVersion) -> None:
    lib = pydantic_v1 if pydantic_version == "v1" else pydantic_v2

    class Model(lib.BaseModel):  # type: ignore[misc, name-defined]
        a: int
        b: int = lib.Field(default=1)
        c: int = lib.Field(default_factory=lambda: 3)

    @post("/")
    async def handler(data: Model) -> dict[str, int]:
        return {"a": data.a, "b": data.b, "c": data.c}

    with create_test_client([handler]) as client:
        schema = client.app.openapi_schema.components.schemas["test_model_defaults.Model"]
        res = client.post("/", json={"a": 5})
        assert res.status_code == 201
        assert res.json() == {"a": 5, "b": 1, "c": 3}
        assert schema.required == ["a"]
        assert schema.properties["b"].default == 1
        assert schema.properties["c"].default is None


@pytest.mark.parametrize("with_dto", [True, False])
def test_v2_computed_fields(with_dto: bool) -> None:
    # https://github.com/litestar-org/litestar/issues/3656

    class Model(pydantic_v2.BaseModel):
        foo: int = 1

        @pydantic_v2.computed_field
        def bar(self) -> int:
            return 2

        @pydantic_v2.computed_field(examples=[1], json_schema_extra={"title": "this is computed"})
        def baz(self) -> int:
            return 3

    @get("/", return_dto=PydanticDTO[Model] if with_dto else None)
    async def handler() -> Model:
        return Model()

    component_name = "HandlerModelResponseBody" if with_dto else "test_v2_computed_fields.Model"

    with create_test_client([handler]) as client:
        schema = client.app.openapi_schema.components.schemas[component_name]
        res = client.get("/")
        assert list(schema.properties.keys()) == ["foo", "bar", "baz"]
        assert schema.properties["baz"].title == "this is computed"
        assert schema.properties["baz"].examples == [1]
        assert res.json() == {"foo": 1, "bar": 2, "baz": 3}
