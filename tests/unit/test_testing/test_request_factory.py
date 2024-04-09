import json
from dataclasses import dataclass
from typing import Callable, Dict

import msgspec
import pytest

from litestar import HttpMethod, Litestar, get
from litestar.datastructures import Cookie, MultiDict
from litestar.enums import ParamType, RequestEncodingType
from litestar.serialization import encode_json
from litestar.testing import RequestFactory
from litestar.types import DataContainerType
from tests.models import (
    DataclassPerson,
    DataclassPersonFactory,
    DataclassPetFactory,
    MsgSpecStructPerson,
)

_DEFAULT_REQUEST_FACTORY_URL = "http://test.org:3000/"
pet = DataclassPetFactory.build()


async def test_request_factory_empty_body() -> None:
    request = RequestFactory().post(data={})
    await request.body()


def test_request_factory_no_cookie_header() -> None:
    headers: Dict[str, str] = {}
    RequestFactory._create_cookie_header(headers)
    assert not headers


def test_request_factory_str_cookie_header() -> None:
    headers: Dict[str, str] = {}
    cookie_as_str = "test=cookie; litestar=cookie"
    RequestFactory._create_cookie_header(headers, cookie_as_str)
    assert headers[ParamType.COOKIE] == cookie_as_str


def test_request_factory_cookie_list_header() -> None:
    headers: Dict[str, str] = {}
    cookie_list = [Cookie(key="test", value="cookie"), Cookie(key="litestar", value="cookie", path="/test")]
    RequestFactory._create_cookie_header(headers, cookie_list)
    assert headers[ParamType.COOKIE] == "test=cookie; Path=/; SameSite=lax; litestar=cookie; Path=/test; SameSite=lax"


def test_request_factory_build_headers() -> None:
    headers = {
        "header1": "value1",
        "header2": "value2",
    }
    built_headers = RequestFactory()._build_headers(headers)

    assert len(built_headers) == len(headers.keys())

    for key, value in built_headers:
        decoded_key = key.decode("latin1")
        decoded_value = value.decode("latin1")
        assert decoded_key in headers
        assert headers[decoded_key] == decoded_value


@pytest.mark.parametrize("data_cls", [DataclassPerson, MsgSpecStructPerson])
async def test_request_factory_create_with_data(data_cls: DataContainerType) -> None:
    person_data = msgspec.json.decode(encode_json(DataclassPersonFactory.build()))
    request = RequestFactory()._create_request_with_data(
        HttpMethod.POST,
        "/",
        data=data_cls(**person_data),  # type: ignore[operator]
    )
    body = await request.body()
    assert json.loads(body) == person_data


async def test_request_factory_create_with_data_with_custom_encoder() -> None:
    class Foo:
        bar: str = "baz"

    request = RequestFactory(app=Litestar(type_encoders={Foo: lambda f: {"bar": f.bar}}))._create_request_with_data(
        HttpMethod.POST,
        "/",
        data=Foo(),  # type: ignore[arg-type]
    )

    body = await request.body()
    assert json.loads(body) == {"bar": "baz"}


@pytest.mark.parametrize(
    "request_media_type, verify_data",
    [
        [RequestEncodingType.JSON, lambda data: json.loads(data) == msgspec.to_builtins(pet)],
        [RequestEncodingType.MULTI_PART, lambda data: "Content-Disposition" in data],
        [
            RequestEncodingType.URL_ENCODED,
            lambda data: data == f"name={pet.name}&age={pet.age}&species={pet.species.value}",
        ],
    ],
)
async def test_request_factory_create_with_content_type(
    request_media_type: RequestEncodingType, verify_data: Callable[[str], bool]
) -> None:
    request = RequestFactory()._create_request_with_data(
        HttpMethod.POST,
        "/",
        data=msgspec.to_builtins(pet),
        request_media_type=request_media_type,
    )
    assert request.headers["Content-Type"].startswith(request_media_type.value)
    body = await request.body()
    assert verify_data(body.decode("utf-8"))


def test_request_factory_create_with_default_params() -> None:
    request = RequestFactory().get()
    assert isinstance(request.app, Litestar)
    assert request.url == request.base_url == _DEFAULT_REQUEST_FACTORY_URL
    assert request.method == HttpMethod.GET
    assert request.state.keys() == {"_ls_connection_state"}
    assert not request.query_params
    assert not request.path_params
    assert request.route_handler
    assert request.scope["http_version"] == "1.1"
    assert request.scope["raw_path"] == b"/"


def test_request_factory_create_with_params() -> None:
    @dataclass
    class User:
        pass

    @dataclass
    class Auth:
        pass

    @get("/path")
    def handler() -> None: ...

    app = Litestar(route_handlers=[])
    server = "litestar.org"
    port = 5000
    root_path = "/root"
    path = "/path"
    user = User()
    auth = Auth()
    scheme = "https"
    session = {"param1": "a", "param2": 2}
    state = {"weather": "sunny"}
    path_params = {"param": "a"}
    request = RequestFactory(app, server, port, root_path, scheme).get(
        path,
        session=session,
        user=user,
        auth=auth,
        state=state,
        path_params=path_params,
        http_version="2.0",
        route_handler=handler,
    )

    assert request.app == app
    assert request.base_url == f"{scheme}://{server}:{port}{root_path}/"
    assert request.url == f"{scheme}://{server}:{port}{root_path}{path}"
    assert request.method == HttpMethod.GET
    assert request.query_params == MultiDict()
    assert request.user == user
    assert request.auth == auth
    assert request.session == session
    assert request.state.weather == "sunny"
    assert request.path_params == path_params
    assert request.route_handler == handler
    assert request.scope["http_version"] == "2.0"
    assert request.scope["raw_path"] == path.encode("ascii")


def test_request_factory_get() -> None:
    query_params = {"p1": "a", "p2": 2, "p3": ["c", "d"]}
    headers = {"header1": "value1"}
    request = RequestFactory().get(headers=headers, query_params=query_params)  # type: ignore[arg-type]
    assert request.method == HttpMethod.GET
    assert request.url == f"{_DEFAULT_REQUEST_FACTORY_URL}?p1=a&p2=2&p3=c&p3=d"
    assert len(request.headers.keys()) == 1
    assert request.headers.get("header1") == "value1"


def test_request_factory_delete() -> None:
    headers = {"header1": "value1"}
    request = RequestFactory().delete(headers=headers)
    assert request.method == HttpMethod.DELETE
    assert request.url == _DEFAULT_REQUEST_FACTORY_URL
    assert len(request.headers.keys()) == 1
    assert request.headers.get("header1") == "value1"


@pytest.mark.parametrize(
    "factory, method",
    [
        (RequestFactory().post, HttpMethod.POST),
        (RequestFactory().put, HttpMethod.PUT),
        (RequestFactory().patch, HttpMethod.PATCH),
    ],
)
async def test_request_factory_post_put_patch(factory: Callable, method: HttpMethod) -> None:
    headers = {"header1": "value1"}
    request = factory("/", headers=headers, data=pet)
    assert request.method == method
    # Headers should include "header1" and "Content-Type"
    assert len(request.headers.keys()) == 3
    assert request.headers.get("header1") == "value1"
    body = await request.body()
    assert json.loads(body) == msgspec.to_builtins(pet)
