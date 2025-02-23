from dataclasses import dataclass
from typing import Annotated, Generic, Optional, TypeVar

import pytest
from attr import define
from typing_extensions import TypedDict

from litestar import get, post
from litestar._signature import SignatureModel
from litestar.di import Provide
from litestar.enums import ParamType
from litestar.exceptions import ImproperlyConfiguredException, ValidationException
from litestar.params import Dependency, Parameter
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.testing import RequestFactory, create_test_client
from litestar.utils.signature import ParsedSignature


def test_parses_values_from_connection_kwargs_raises() -> None:
    def fn(a: int) -> None:
        pass

    model = SignatureModel.create(
        dependency_name_set=set(),
        fn=fn,
        data_dto=None,
        parsed_signature=ParsedSignature.from_fn(fn, {}),
        type_decoders=[],
    )
    with pytest.raises(ValidationException):
        model.parse_values_from_connection_kwargs(connection=RequestFactory().get(), kwargs={"a": "not an int"})


def test_create_signature_validation() -> None:
    @get()
    def my_fn(typed: int, untyped) -> None:  # type: ignore[no-untyped-def]
        pass

    with pytest.raises(ImproperlyConfiguredException):
        SignatureModel.create(
            dependency_name_set=set(),
            fn=my_fn.fn,
            data_dto=None,
            parsed_signature=ParsedSignature.from_fn(my_fn.fn, {}),
            type_decoders=[],
        )


def test_dependency_validation_failure_raises_500() -> None:
    dependencies = {"dep": Provide(lambda: "thirteen", sync_to_thread=False)}

    @get("/")
    def test(dep: int, param: int, optional_dep: Optional[int] = Dependency()) -> None: ...

    with create_test_client(
        route_handlers=[test],
        dependencies=dependencies,
        debug=False,
    ) as client:
        response = client.get("/?param=13")

    assert response.json() == {"detail": "Internal Server Error", "status_code": HTTP_500_INTERNAL_SERVER_ERROR}


def test_validation_failure_raises_400() -> None:
    dependencies = {"dep": Provide(lambda: 13, sync_to_thread=False)}

    @get("/")
    def test(dep: int, param: int, optional_dep: Optional[int] = Dependency(default=None)) -> None: ...

    with create_test_client(route_handlers=[test], dependencies=dependencies) as client:
        response = client.get("/?param=thirteen")

    assert response.json() == {
        "detail": "Validation failed for GET /?param=thirteen",
        "extra": [{"key": "param", "message": "Expected `int`, got `str`", "source": "query"}],
        "status_code": 400,
    }


def test_invalid_path_parameter() -> None:
    @get("/{param:int}")
    def test(param: Annotated[int, Parameter(le=10)]) -> None: ...

    with create_test_client(route_handlers=[test]) as client:
        response = client.get("/11")

    assert response.json() == {
        "detail": "Validation failed for GET /11",
        "extra": [{"key": "param", "message": "Expected `int` <= 10", "source": "path"}],
        "status_code": 400,
    }


def test_client_backend_error_precedence_over_server_error() -> None:
    dependencies = {
        "dep": Provide(lambda: "thirteen", sync_to_thread=False),
        "optional_dep": Provide(lambda: "thirty-one", sync_to_thread=False),
    }

    @get("/")
    def test(dep: int, param: int, optional_dep: Optional[int] = Dependency()) -> None: ...

    with create_test_client(route_handlers=[test], dependencies=dependencies) as client:
        response = client.get("/?param=thirteen")

    assert response.json() == {
        "detail": "Validation failed for GET /?param=thirteen",
        "extra": [{"key": "param", "message": "Expected `int`, got `str`", "source": "query"}],
        "status_code": 400,
    }


def test_validation_error_exception_key() -> None:
    from dataclasses import dataclass

    @dataclass
    class OtherChild:
        val: list[int]

    @dataclass
    class Child:
        val: int
        other_val: int

    @dataclass
    class Parent:
        child: Child
        other_child: OtherChild

    @get("/")
    def handler(data: Parent) -> None:
        pass

    model = SignatureModel.create(
        dependency_name_set=set(),
        fn=handler,  # type: ignore[arg-type]
        data_dto=None,
        parsed_signature=ParsedSignature.from_fn(handler.fn, {}),
        type_decoders=[],
    )

    with pytest.raises(ValidationException) as exc_info:
        model.parse_values_from_connection_kwargs(
            connection=RequestFactory().get(route_handler=handler), kwargs={"data": {"child": {}, "other_child": {}}}
        )

    assert isinstance(exc_info.value.extra, list)
    assert exc_info.value.extra[0]["key"] == "child"


def test_invalid_input_attrs() -> None:
    @define
    class OtherChild:
        val: list[int]

    @define
    class Child:
        val: int
        other_val: int

    @define
    class Parent:
        child: Child
        other_child: OtherChild

    @post("/")
    def test(
        data: Parent,
        int_param: int,
        int_header: int = Parameter(header="X-SOME-INT"),
        int_cookie: int = Parameter(cookie="int-cookie"),
    ) -> None: ...

    with create_test_client(route_handlers=[test]) as client:
        client.cookies.update({"int-cookie": "cookie"})
        response = client.post(
            "/",
            json={"child": {"val": "a", "other_val": "b"}, "other_child": {"val": [1, "c"]}},
            params={"int_param": "param"},
            headers={"X-SOME-INT": "header"},
        )

        assert response.status_code == HTTP_400_BAD_REQUEST

        data = response.json()

        assert data
        assert data["extra"] == [
            {"message": "Expected `int`, got `str`", "key": "child.val", "source": "body"},
            {"message": "Expected `int`, got `str`", "key": "int_param", "source": "query"},
            {"message": "Expected `int`, got `str`", "key": "int_header", "source": "header"},
            {"message": "Expected `int`, got `str`", "key": "int_cookie", "source": "cookie"},
        ]


def test_invalid_input_dataclass() -> None:
    @dataclass
    class OtherChild:
        val: list[int]

    @dataclass
    class Child:
        val: int
        other_val: int

    @dataclass
    class Parent:
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

    with create_test_client(route_handlers=[test]) as client:
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
        assert data["extra"] == [
            {"message": "Expected `int`, got `str`", "key": "child.val", "source": "body"},
            {"message": "Expected `int`, got `str`", "key": "int_param", "source": "query"},
            {"message": "Expected `str` of length >= 2", "key": "length_param", "source": "query"},
            {"message": "Expected `int`, got `str`", "key": "int_header", "source": "header"},
            {"message": "Expected `int`, got `str`", "key": "int_cookie", "source": "cookie"},
        ]


def test_invalid_input_typed_dict() -> None:
    class OtherChild(TypedDict):
        val: list[int]

    class Child(TypedDict):
        val: int
        other_val: int

    class Parent(TypedDict):
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

    with create_test_client(route_handlers=[test]) as client:
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
        assert data["extra"] == [
            {"message": "Expected `int`, got `str`", "key": "child.val", "source": "body"},
            {"message": "Expected `int`, got `str`", "key": "int_param", "source": "query"},
            {"message": "Expected `str` of length >= 2", "key": "length_param", "source": "query"},
            {"message": "Expected `int`, got `str`", "key": "int_header", "source": "header"},
            {"message": "Expected `int`, got `str`", "key": "int_cookie", "source": "cookie"},
        ]


def test_parse_values_from_connection_kwargs_with_multiple_errors() -> None:
    def fn(a: Annotated[int, Parameter(gt=5)], b: Annotated[int, Parameter(lt=5)]) -> None:
        pass

    model = SignatureModel.create(
        dependency_name_set=set(),
        fn=fn,
        data_dto=None,
        parsed_signature=ParsedSignature.from_fn(fn, {}),
        type_decoders=[],
    )
    with pytest.raises(ValidationException) as exc:
        model.parse_values_from_connection_kwargs(connection=RequestFactory().get(), kwargs={"a": 0, "b": 9})

    assert exc.value.extra == [
        {"message": "Expected `int` >= 6", "key": "a", "source": ParamType.QUERY},
        {"message": "Expected `int` <= 4", "key": "b", "source": ParamType.QUERY},
    ]


def test_validate_subscribed_generics() -> None:
    T = TypeVar("T")

    class Foo(Generic[T]):
        pass

    @get("/")
    async def something(foo: Foo[str] = Foo()) -> None:
        return None

    with create_test_client([something]) as client:
        assert client.get("/").status_code == 200


def test_separate_model_namespace() -> None:
    # https://github.com/litestar-org/litestar/issues/3593

    async def provide_connection() -> str:
        return "connection"

    @get("/connection", dependencies={"connection": provide_connection})
    async def get_connection(connection: str) -> str:
        return connection

    async def provide_deserializer() -> str:
        return "deserializer"

    @get("/deserializer", dependencies={"deserializer": provide_deserializer})
    async def get_deserializer(deserializer: int) -> str:
        return deserializer  # type: ignore[return-value]

    with create_test_client([get_connection, get_deserializer], raise_server_exceptions=True, debug=True) as client:
        assert client.get("/connection").text == "connection"
        res = client.get("/deserializer")
        assert res.status_code == 500
        assert "Expected `int`, got `str` - at `$.deserializer`" in res.text
