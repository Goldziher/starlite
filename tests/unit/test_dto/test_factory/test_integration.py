# ruff: noqa: UP007, UP006
from __future__ import annotations

from dataclasses import dataclass, field
from types import ModuleType
from typing import TYPE_CHECKING, Callable, Dict, Generic, List, Optional, Sequence, TypeVar, cast
from unittest.mock import MagicMock
from uuid import UUID

import msgspec
import pytest
from msgspec import Struct
from typing_extensions import Annotated

from litestar import Controller, Response, get, patch, post
from litestar.connection.request import Request
from litestar.datastructures import UploadFile
from litestar.dto import DataclassDTO, DTOConfig, DTOData, MsgspecDTO, dto_field
from litestar.dto.types import RenameStrategy
from litestar.enums import MediaType, RequestEncodingType
from litestar.pagination import ClassicPagination, CursorPagination, OffsetPagination
from litestar.params import Body
from litestar.serialization import encode_json
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from typing import Any


def test_url_encoded_form_data(use_experimental_dto_backend: bool) -> None:
    @dataclass()
    class User:
        name: str
        age: int
        read_only: str = field(default="read-only", metadata=dto_field("read-only"))

    class UserDTO(DataclassDTO[User]):
        config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

    @post(dto=UserDTO, signature_types=[User])
    def handler(data: User = Body(media_type=RequestEncodingType.URL_ENCODED)) -> User:
        return data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post(
            "/",
            content=b"id=1&name=John&age=42&read_only=whoops",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.json() == {"name": "John", "age": 42, "read_only": "read-only"}


async def test_multipart_encoded_form_data(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class Payload:
        file: UploadFile
        forbidden: UploadFile = field(
            default=UploadFile(content_type="text/plain", filename="forbidden", file_data=b"forbidden"),
            metadata=dto_field("read-only"),
        )

    class PayloadDTO(DataclassDTO[Payload]):
        config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

    @post(dto=PayloadDTO, return_dto=None, signature_types=[Payload], media_type=MediaType.TEXT)
    async def handler(data: Payload = Body(media_type=RequestEncodingType.MULTI_PART)) -> bytes:
        return await data.forbidden.read()

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post(
            "/",
            files={"file": b"abc123", "forbidden": b"123abc"},
        )
        assert response.content == b"forbidden"


def test_renamed_field(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class Foo:
        bar: str

    config = DTOConfig(rename_fields={"bar": "baz"}, experimental_codegen_backend=use_experimental_dto_backend)
    dto = DataclassDTO[Annotated[Foo, config]]

    @post(dto=dto, signature_types=[Foo])
    def handler(data: Foo) -> Foo:
        assert data.bar == "hello"
        return data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json={"baz": "hello"})
        assert response.json() == {"baz": "hello"}


def test_renamed_field_nested(use_experimental_dto_backend: bool, create_module: Callable[[str], ModuleType]) -> None:
    # https://github.com/litestar-org/litestar/issues/2721
    module = create_module(
        """
from dataclasses import dataclass
from typing import List

@dataclass
class Bar:
    id: str

@dataclass
class Foo:
    id: str
    bar: Bar
    bars: List[Bar]
"""
    )

    Foo = module.Foo

    config = DTOConfig(
        rename_fields={"id": "foo_id", "bar.id": "bar_id", "bars.0.id": "bars_id"},
        experimental_codegen_backend=use_experimental_dto_backend,
    )
    dto = DataclassDTO[Annotated[Foo, config]]  # type: ignore[valid-type]

    @post(dto=dto, signature_types=[Foo])
    def handler(data: Foo) -> Foo:  # type: ignore[valid-type]
        return data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json={"foo_id": "1", "bar": {"bar_id": "2"}, "bars": [{"bars_id": "3"}]})
        assert response.json() == {"foo_id": "1", "bar": {"bar_id": "2"}, "bars": [{"bars_id": "3"}]}


@dataclass
class Spam:
    main_id: str = "spam-id"


@dataclass
class Fzop:
    bar: str = "hello"
    SPAM: str = "bye"
    spam_bar: str = "welcome"
    spam_model: Optional[Spam] = None


@pytest.mark.parametrize(
    "rename_strategy, instance, tested_fields, data",
    [
        ("upper", Fzop(bar="hi"), ["BAR"], {"BAR": "hi"}),
        ("lower", Fzop(SPAM="goodbye"), ["spam"], {"spam": "goodbye"}),
        (lambda x: x[::-1], Fzop(bar="h", SPAM="bye!"), ["rab", "MAPS"], {"rab": "h", "MAPS": "bye!"}),
        ("camel", Fzop(spam_bar="star"), ["spamBar"], {"spamBar": "star"}),
        ("pascal", Fzop(spam_bar="star"), ["SpamBar"], {"SpamBar": "star"}),
        ("camel", Fzop(spam_model=Spam()), ["spamModel"], {"spamModel": {"mainId": "spam-id"}}),
        (
            "kebab",
            Fzop(spam_bar="star", spam_model=Spam()),
            ["spam-bar", "spam-model"],
            {"spam-bar": "star", "spam-model": {"main-id": "spam-id"}},
        ),
    ],
)
def test_fields_alias_generator(
    rename_strategy: RenameStrategy,
    instance: Fzop,
    tested_fields: list[str],
    data: dict[str, str],
    use_experimental_dto_backend: bool,
) -> None:
    DataclassDTO._dto_backends = {}
    config = DTOConfig(rename_strategy=rename_strategy, experimental_codegen_backend=use_experimental_dto_backend)
    dto = DataclassDTO[Annotated[Fzop, config]]

    @post(dto=dto)
    def handler(data: Fzop) -> Fzop:
        assert data.bar == instance.bar
        assert data.SPAM == instance.SPAM
        return data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json=data)
        for f in tested_fields:
            assert response.json()[f] == data[f]


def test_dto_data_injection(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class Foo:
        bar: str

    config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

    @post(dto=DataclassDTO[Annotated[Foo, config]], return_dto=None, signature_types=[Foo])
    def handler(data: DTOData[Foo]) -> Foo:
        assert isinstance(data, DTOData)
        assert data.as_builtins() == {"bar": "hello"}
        assert isinstance(data.create_instance(), Foo)
        return data.create_instance()

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json={"bar": "hello"})
        assert response.json() == {"bar": "hello"}


@dataclass
class NestedFoo:
    bar: str
    baz: str


@dataclass
class NestingBar:
    foo: NestedFoo


def test_dto_data_injection_with_nested_model(use_experimental_dto_backend: bool) -> None:
    @post(
        dto=DataclassDTO[
            Annotated[
                NestingBar, DTOConfig(exclude={"foo.baz"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ],
        return_dto=None,
    )
    def handler(data: DTOData[NestingBar]) -> Dict[str, Any]:
        assert isinstance(data, DTOData)
        return cast("dict[str, Any]", data.as_builtins())

    with create_test_client(route_handlers=[handler]) as client:
        resp = client.post("/", json={"foo": {"bar": "hello"}})
        assert resp.status_code == 201
        assert resp.json() == {"foo": {"bar": "hello"}}


def test_dto_data_create_instance_nested_kwargs(use_experimental_dto_backend: bool) -> None:
    @post(
        dto=DataclassDTO[
            Annotated[
                NestingBar, DTOConfig(exclude={"foo.baz"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ],
        return_dto=None,
    )
    def handler(data: DTOData[NestingBar]) -> NestingBar:
        assert isinstance(data, DTOData)
        result = data.create_instance(foo__baz="world")
        assert result.foo.baz == "world"
        return result

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json={"foo": {"bar": "hello"}})
        assert response.status_code == 201
        assert response.json() == {"foo": {"bar": "hello", "baz": "world"}}


@dataclass
class User:
    name: str
    age: int
    read_only: str = field(default="read-only", metadata=dto_field("read-only"))


def test_dto_data_with_url_encoded_form_data(use_experimental_dto_backend: bool) -> None:
    config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

    @post(dto=DataclassDTO[Annotated[User, config]])
    def handler(data: DTOData[User] = Body(media_type=RequestEncodingType.URL_ENCODED)) -> User:
        return data.create_instance()

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post(
            "/",
            content=b"id=1&name=John&age=42&read_only=whoops",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.json() == {"name": "John", "age": 42, "read_only": "read-only"}


RenamedBarT = TypeVar("RenamedBarT")


@dataclass
class GenericRenamedBar(Generic[RenamedBarT]):
    bar: str
    spam_bar: RenamedBarT
    foo_foo: str


@dataclass
class InnerBar:
    best_greeting: str


@dataclass
class RenamedBar(GenericRenamedBar[InnerBar]):
    pass


def test_dto_data_create_instance_renamed_fields(use_experimental_dto_backend: bool) -> None:
    @post(
        dto=DataclassDTO[
            Annotated[
                RenamedBar,
                DTOConfig(
                    exclude={"foo_foo"},
                    rename_strategy="camel",
                    experimental_codegen_backend=use_experimental_dto_backend,
                ),
            ]
        ],
        return_dto=DataclassDTO[
            Annotated[
                RenamedBar,
                DTOConfig(rename_strategy="camel", experimental_codegen_backend=use_experimental_dto_backend),
            ]
        ],
    )
    def handler(data: DTOData[RenamedBar]) -> RenamedBar:
        assert isinstance(data, DTOData)
        result = data.create_instance(foo_foo="world")
        assert result.foo_foo == "world"
        assert result.spam_bar.best_greeting == "hello world"
        return result

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json={"bar": "hello", "spamBar": {"bestGreeting": "hello world"}})
        assert response.status_code == 201
        assert response.json() == {"bar": "hello", "fooFoo": "world", "spamBar": {"bestGreeting": "hello world"}}


def test_dto_data_with_patch_request(use_experimental_dto_backend: bool) -> None:
    class PatchDTO(DataclassDTO[Annotated[User, DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)]]):
        config = DTOConfig(partial=True)

    @patch(dto=PatchDTO, return_dto=None)
    def handler(data: DTOData[User]) -> User:
        return data.update_instance(User(name="John", age=42))

    with create_test_client(route_handlers=[handler]) as client:
        response = client.patch("/", json={"age": 41, "read_only": "whoops"})
        assert response.json() == {"name": "John", "age": 41, "read_only": "read-only"}


@dataclass
class UniqueModelName:
    id: int
    foo: str


def test_dto_openapi_with_unique_handler_names(use_experimental_dto_backend: bool) -> None:
    @post(
        dto=DataclassDTO[
            Annotated[
                UniqueModelName, DTOConfig(exclude={"id"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ],
        return_dto=DataclassDTO[UniqueModelName],
        signature_namespace={"UniqueModelName": UniqueModelName},
    )
    def handler(data: UniqueModelName) -> UniqueModelName:
        return data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.get("/schema/openapi.json")
        schemas = list(response.json()["components"]["schemas"].values())
        assert len(schemas) == 2
        assert schemas[0]["title"] == "HandlerUniqueModelNameRequestBody"
        assert schemas[1]["title"] == "HandlerUniqueModelNameResponseBody"


@dataclass
class SharedModelName:
    id: int
    foo: str


def test_dto_openapi_without_unique_handler_names(use_experimental_dto_backend: bool) -> None:
    write_dto = DataclassDTO[
        Annotated[SharedModelName, DTOConfig(exclude={"id"}, experimental_codegen_backend=use_experimental_dto_backend)]
    ]
    read_dto = DataclassDTO[SharedModelName]

    @post(dto=write_dto, return_dto=read_dto)
    def handler(data: SharedModelName) -> SharedModelName:
        return data

    class MyController(Controller):
        path = "/sub-path"

        @post(dto=write_dto, return_dto=read_dto)
        def handler(self, data: SharedModelName) -> SharedModelName:
            return data

    with create_test_client(route_handlers=[handler, MyController]) as client:
        response = client.get("/schema/openapi.json")
        schemas = list(response.json()["components"]["schemas"].values())
        assert len(schemas) == 4
        assert schemas[0]["title"] == "HandlerSharedModelNameRequestBody"
        assert schemas[1]["title"] == "HandlerSharedModelNameResponseBody"
        assert (
            schemas[2]["title"]
            == "tests.unit.test_dto.test_factory.test_integration.test_dto_openapi_without_unique_handler_names.<locals>.MyController.handlerSharedModelNameRequestBody"
        )
        assert (
            schemas[3]["title"]
            == "tests.unit.test_dto.test_factory.test_integration.test_dto_openapi_without_unique_handler_names.<locals>.MyController.handlerSharedModelNameResponseBody"
        )


def test_url_encoded_form_data_patch_request(use_experimental_dto_backend: bool) -> None:
    @dataclass()
    class User:
        name: str
        age: int
        read_only: str = field(default="read-only", metadata=dto_field("read-only"))

    dto = DataclassDTO[
        Annotated[User, DTOConfig(partial=True, experimental_codegen_backend=use_experimental_dto_backend)]
    ]

    @post(dto=dto, return_dto=None, signature_types=[User])
    def handler(data: DTOData[User] = Body(media_type=RequestEncodingType.URL_ENCODED)) -> Dict[str, Any]:
        return data.as_builtins()  # type:ignore[no-any-return]

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post(
            "/",
            content=b"name=John&read_only=whoops",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.json() == {"name": "John"}


def test_dto_with_generic_sequence_annotations(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class User:
        name: str
        age: int

    @post(
        dto=DataclassDTO[Annotated[User, DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)]],
        signature_types=[User],
    )
    def handler(data: Sequence[User]) -> Sequence[User]:
        return data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json=[{"name": "John", "age": 42}])
        assert response.json() == [{"name": "John", "age": 42}]


def test_dto_private_fields(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class Foo:
        bar: str
        _baz: int

    mock = MagicMock()

    @post(
        dto=DataclassDTO[Annotated[Foo, DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)]],
        signature_types=[Foo],
    )
    def handler(data: DTOData[Foo]) -> Foo:
        mock.received_data = data.as_builtins()
        return data.create_instance(_baz=42)

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json={"bar": "hello", "_baz": "world"})
        assert response.status_code == 201
        assert response.json() == {"bar": "hello"}

    assert mock.received_data == {"bar": "hello"}


def test_dto_private_fields_disabled(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class Foo:
        bar: str
        _baz: int

    @post(
        dto=DataclassDTO[
            Annotated[
                Foo,
                DTOConfig(underscore_fields_private=False, experimental_codegen_backend=use_experimental_dto_backend),
            ]
        ],
        signature_types=[Foo],
    )
    def handler(data: Foo) -> Foo:
        return data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json={"bar": "hello", "_baz": 42})
        assert response.status_code == 201
        assert response.json() == {"bar": "hello", "_baz": 42}


def test_dto_concrete_builtin_collection_types(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class Foo:
        bar: dict
        baz: list

    @post(
        dto=DataclassDTO[
            Annotated[
                Foo,
                DTOConfig(underscore_fields_private=False, experimental_codegen_backend=use_experimental_dto_backend),
            ]
        ],
        signature_types=[Foo],
    )
    def handler(data: Foo) -> Foo:
        return data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post("/", json={"bar": {"a": 1, "b": [1, 2, 3]}, "baz": [4, 5, 6]})
        assert response.status_code == 201
        assert response.json() == {"bar": {"a": 1, "b": [1, 2, 3]}, "baz": [4, 5, 6]}


@dataclass
class PaginatedUser:
    name: str
    age: int


def test_dto_classic_pagination(use_experimental_dto_backend: bool) -> None:
    @get(
        dto=DataclassDTO[
            Annotated[
                PaginatedUser, DTOConfig(exclude={"age"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ]
    )
    def handler() -> ClassicPagination[PaginatedUser]:
        return ClassicPagination(
            items=[PaginatedUser(name="John", age=42), PaginatedUser(name="Jane", age=43)],
            page_size=2,
            current_page=1,
            total_pages=20,
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json() == {
            "items": [{"name": "John"}, {"name": "Jane"}],
            "page_size": 2,
            "current_page": 1,
            "total_pages": 20,
        }


def test_dto_cursor_pagination(use_experimental_dto_backend: bool) -> None:
    uuid = UUID("00000000-0000-0000-0000-000000000000")

    @get(
        dto=DataclassDTO[
            Annotated[
                PaginatedUser, DTOConfig(exclude={"age"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ]
    )
    def handler() -> CursorPagination[UUID, PaginatedUser]:
        return CursorPagination(
            items=[PaginatedUser(name="John", age=42), PaginatedUser(name="Jane", age=43)],
            results_per_page=2,
            cursor=uuid,
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json() == {
            "items": [{"name": "John"}, {"name": "Jane"}],
            "results_per_page": 2,
            "cursor": "00000000-0000-0000-0000-000000000000",
        }


def test_dto_offset_pagination(use_experimental_dto_backend: bool) -> None:
    @get(
        dto=DataclassDTO[
            Annotated[
                PaginatedUser, DTOConfig(exclude={"age"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ]
    )
    def handler() -> OffsetPagination[PaginatedUser]:
        return OffsetPagination(
            items=[PaginatedUser(name="John", age=42), PaginatedUser(name="Jane", age=43)],
            limit=2,
            offset=0,
            total=20,
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json() == {
            "items": [{"name": "John"}, {"name": "Jane"}],
            "limit": 2,
            "offset": 0,
            "total": 20,
        }


T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")


@dataclass
class Wrapped(Generic[T, V]):
    data: T
    other: V


def test_dto_generic_dataclass_wrapped_list_response(use_experimental_dto_backend: bool) -> None:
    @get(dto=DataclassDTO[Annotated[PaginatedUser, DTOConfig(exclude={"age"})]])
    def handler() -> Wrapped[List[PaginatedUser], int]:
        return Wrapped(
            data=[PaginatedUser(name="John", age=42), PaginatedUser(name="Jane", age=43)],
            other=2,
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json() == {"data": [{"name": "John"}, {"name": "Jane"}], "other": 2}


def test_dto_generic_dataclass_wrapped_scalar_response(use_experimental_dto_backend: bool) -> None:
    @get(
        dto=DataclassDTO[
            Annotated[
                PaginatedUser, DTOConfig(exclude={"age"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ]
    )
    def handler() -> Wrapped[PaginatedUser, int]:
        return Wrapped(
            data=PaginatedUser(name="John", age=42),
            other=2,
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json() == {"data": {"name": "John"}, "other": 2}


@dataclass
class WrappedWithDict(Generic[K, V, T]):
    data: T
    other: Dict[K, V]


def test_dto_generic_dataclass_wrapped_scalar_response_with_additional_mapping_data(
    use_experimental_dto_backend: bool,
) -> None:
    @get(
        dto=DataclassDTO[
            Annotated[
                PaginatedUser, DTOConfig(exclude={"age"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ]
    )
    def handler() -> WrappedWithDict[str, int, PaginatedUser]:
        return WrappedWithDict(
            data=PaginatedUser(name="John", age=42),
            other={"a": 1, "b": 2},
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json() == {"data": {"name": "John"}, "other": {"a": 1, "b": 2}}


def test_dto_response_wrapped_scalar_return_type(use_experimental_dto_backend: bool) -> None:
    @get(
        dto=DataclassDTO[
            Annotated[
                PaginatedUser, DTOConfig(exclude={"age"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ]
    )
    def handler() -> Response[PaginatedUser]:
        return Response(content=PaginatedUser(name="John", age=42))

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json() == {"name": "John"}


def test_dto_response_wrapped_collection_return_type(use_experimental_dto_backend: bool) -> None:
    @get(
        dto=DataclassDTO[
            Annotated[
                PaginatedUser, DTOConfig(exclude={"age"}, experimental_codegen_backend=use_experimental_dto_backend)
            ]
        ]
    )
    def handler() -> Response[List[PaginatedUser]]:
        return Response(content=[PaginatedUser(name="John", age=42), PaginatedUser(name="Jane", age=43)])

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.json() == [{"name": "John"}, {"name": "Jane"}]


def test_schema_required_fields_with_msgspec_dto(use_experimental_dto_backend: bool) -> None:
    class MsgspecUser(Struct):
        age: int
        name: str

    class UserDTO(MsgspecDTO[MsgspecUser]):
        config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

    @post(dto=UserDTO, return_dto=None, signature_types=[MsgspecUser])
    def handler(data: MsgspecUser, request: Request) -> dict:
        schema = request.app.openapi_schema
        return schema.to_schema()

    with create_test_client(handler) as client:
        data = MsgspecUser(name="A", age=10)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        received = client.post(
            "/",
            content=msgspec.json.encode(data),
            headers=headers,
        )
        required = next(iter(received.json()["components"]["schemas"].values()))["required"]
        assert len(required) == 2


def test_schema_required_fields_with_dataclass_dto(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class DataclassUser:
        age: int
        name: str

    class UserDTO(DataclassDTO[DataclassUser]):
        config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

    @post(dto=UserDTO, return_dto=None, signature_types=[DataclassUser])
    def handler(data: DataclassUser, request: Request) -> dict:
        schema = request.app.openapi_schema
        return schema.to_schema()

    with create_test_client(handler) as client:
        data = DataclassUser(name="A", age=10)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        received = client.post(
            "/",
            content=msgspec.json.encode(data),
            headers=headers,
        )
        required = next(iter(received.json()["components"]["schemas"].values()))["required"]
        assert len(required) == 2


def test_schema_required_fields_with_msgspec_dto_and_default_fields(use_experimental_dto_backend: bool) -> None:
    class MsgspecUser(Struct):
        age: int
        name: str = "A"

    class UserDTO(MsgspecDTO[MsgspecUser]):
        config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

    @post(dto=UserDTO, return_dto=None, signature_types=[MsgspecUser])
    def handler(data: MsgspecUser, request: Request) -> dict:
        schema = request.app.openapi_schema
        return schema.to_schema()

    with create_test_client(handler) as client:
        data = MsgspecUser(name="A", age=10)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        received = client.post(
            "/",
            content=msgspec.json.encode(data),
            headers=headers,
        )
        required = next(iter(received.json()["components"]["schemas"].values()))["required"]
        assert required == ["age"]


X = TypeVar("X", bound=Struct)


class ClassicNameStyle(Struct):
    first_name: str
    surname: str


class BoundUser(Struct, Generic[X]):
    age: int
    data: X


class Superuser(BoundUser[ClassicNameStyle]):
    pass


def test_dto_with_msgspec_with_bound_generic_and_inherited_models(use_experimental_dto_backend: bool) -> None:
    @post(dto=MsgspecDTO[Annotated[Superuser, DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)]])
    def handler(data: Superuser) -> Superuser:
        return data

    with create_test_client(handler) as client:
        data = Superuser(data=ClassicNameStyle(first_name="A", surname="B"), age=10)
        received = client.post(
            "/",
            content=encode_json(data),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        assert msgspec.json.decode(received.content, type=Superuser) == data


def test_dto_returning_mapping(use_experimental_dto_backend: bool) -> None:
    @dataclass
    class Lexeme:
        id: int
        name: str

    class LexemeDTO(DataclassDTO[Lexeme]):
        config = DTOConfig(exclude={"id"}, experimental_codegen_backend=use_experimental_dto_backend)

    @get(return_dto=LexemeDTO, signature_types=[Lexeme])
    async def get_definition() -> Dict[str, Lexeme]:
        return {"hello": Lexeme(id=1, name="hello"), "world": Lexeme(id=2, name="world")}

    with create_test_client(route_handlers=[get_definition]) as client:
        response = client.get("/")
        assert response.json() == {"hello": {"name": "hello"}, "world": {"name": "world"}}


def test_data_dto_with_default() -> None:
    """A POST request without Body should inject the default value.

    https://github.com/litestar-org/litestar/issues/2902
    """

    @dataclass
    class Foo:
        foo: str

    @post(path="/", dto=DataclassDTO[Foo], signature_types=[Foo])
    def test(data: Optional[Foo] = None) -> dict:
        return {"foo": data}

    with create_test_client([test]) as client:
        response = client.post("/")
        assert response.json() == {"foo": None}


@pytest.mark.parametrize(
    "field_type, constraint_name, constraint_value, request_data",
    [
        (int, "gt", 2, 2),
        (int, "ge", 2, 1),
        (int, "lt", 2, 2),
        (int, "le", 2, 3),
        (int, "multiple_of", 2, 3),
        (str, "min_length", 2, "1"),
        (str, "max_length", 1, "12"),
        (str, "pattern", r"\d", "a"),
    ],
)
def test_msgspec_dto_copies_constraints(
    field_type: Any, constraint_name: str, constraint_value: Any, request_data: Any, use_experimental_dto_backend: bool
) -> None:
    # https://github.com/litestar-org/litestar/issues/3026
    struct = msgspec.defstruct(
        "Foo",
        fields=[("bar", Annotated[field_type, msgspec.Meta(**{constraint_name: constraint_value})])],  # type: ignore[list-item]
    )

    @post(
        "/",
        dto=Annotated[MsgspecDTO[struct], DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)],  # type: ignore[arg-type, valid-type]
        signature_namespace={"struct": struct},
    )
    def handler(data: struct) -> None:  # type: ignore[valid-type]
        pass

    with create_test_client([handler]) as client:
        assert client.post("/", json={"bar": request_data}).status_code == 400


def test_msgspec_dto_dont_copy_length_constraint_for_partial_dto() -> None:
    class Foo(msgspec.Struct):
        bar: Annotated[str, msgspec.Meta(min_length=2)]
        baz: Annotated[str, msgspec.Meta(max_length=2)]

    class FooDTO(MsgspecDTO[Foo]):
        config = DTOConfig(partial=True)

    @post("/", dto=FooDTO, signature_types={Foo})
    def handler(data: Foo) -> None:
        pass

    with create_test_client([handler]) as client:
        assert client.post("/", json={"bar": "1", "baz": "123"}).status_code == 201
