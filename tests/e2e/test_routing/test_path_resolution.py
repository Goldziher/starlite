from pathlib import Path
from typing import Any, Callable, List, Optional, Type

import httpx
import pytest
from _pytest.monkeypatch import MonkeyPatch

from litestar import Controller, MediaType, Router, delete, get, post
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
)
from litestar.testing import create_test_client


@delete(sync_to_thread=False)
def root_delete_handler() -> None:
    return None


@pytest.mark.parametrize(
    "request_path, router_path, status_code",
    [
        (
            "/path/1/2/sub/c892496f-b1fd-4b91-bdb8-b46f92df1716",
            "/path/{first:int}/{second:str}/sub/{third:uuid}",
            int(HTTP_200_OK),
        ),
        (
            "/path/1/2/sub/2535a9cb-6554-4d85-bb3b-ad38362f63c7/",
            "/path/{first:int}/{second:str}/sub/{third:uuid}/",
            int(HTTP_200_OK),
        ),
        ("/", "/", int(HTTP_200_OK)),
        ("", "", int(HTTP_200_OK)),
        (
            "/a/b/c/d/path/1/2/sub/d4aca431-2e02-4818-824b-a2ddc6a64e9c/",
            "/path/{first:int}/{second:str}/sub/{third:uuid}/",
            int(HTTP_404_NOT_FOUND),
        ),
    ],
)
def test_path_parsing_and_matching(request_path: str, router_path: str, status_code: int) -> None:
    @get(path=router_path)
    def test_method() -> None:
        return None

    with create_test_client(test_method) as client:
        response = client.get(request_path)
        assert response.status_code == status_code


def test_path_parsing_with_ambiguous_paths() -> None:
    @get(path="/{path_param:int}", media_type=MediaType.TEXT)
    def path_param(path_param: int) -> str:
        return str(path_param)

    @get(path="/query_param", media_type=MediaType.TEXT)
    def query_param(value: int) -> str:
        return str(value)

    @get(path="/mixed/{path_param:int}", media_type=MediaType.TEXT)
    def mixed_params(path_param: int, value: int) -> str:
        return str(path_param + value)

    with create_test_client([path_param, query_param, mixed_params]) as client:
        response = client.get("/1")
        assert response.status_code == HTTP_200_OK
        response = client.get("/query_param?value=1")
        assert response.status_code == HTTP_200_OK
        response = client.get("/mixed/1/?value=1")
        assert response.status_code == HTTP_200_OK


@pytest.mark.parametrize(
    "decorator, test_path, decorator_path, delete_handler",
    [
        (get, "", "/something", None),
        (get, "/", "/something", None),
        (get, "", "/", None),
        (get, "/", "/", None),
        (get, "", "", None),
        (get, "/", "", None),
        (get, "", "/something", root_delete_handler),
        (get, "/", "/something", root_delete_handler),
        (get, "", "/", root_delete_handler),
        (get, "/", "/", root_delete_handler),
        (get, "", "", root_delete_handler),
        (get, "/", "", root_delete_handler),
    ],
)
def test_root_route_handler(
    decorator: Type[get], test_path: str, decorator_path: str, delete_handler: Optional[Callable]
) -> None:
    class MyController(Controller):
        path = test_path

        @decorator(path=decorator_path)
        def test_method(self) -> str:
            return "hello"

    with create_test_client([MyController, delete_handler] if delete_handler else MyController) as client:
        response = client.get(decorator_path or test_path)
        assert response.status_code == HTTP_200_OK
        if delete_handler:
            delete_response = client.delete("/")
            assert delete_response.status_code == HTTP_204_NO_CONTENT


def test_handler_multi_paths() -> None:
    @get(path=["/", "/something", "/{some_id:int}", "/something/{some_id:int}"], media_type=MediaType.TEXT)
    def handler_fn(some_id: int = 1) -> str:
        assert some_id
        return str(some_id)

    with create_test_client(handler_fn) as client:
        first_response = client.get("/")
        assert first_response.status_code == HTTP_200_OK
        assert first_response.text == "1"
        second_response = client.get("/2")
        assert second_response.status_code == HTTP_200_OK
        assert second_response.text == "2"
        third_response = client.get("/something")
        assert third_response.status_code == HTTP_200_OK
        assert third_response.text == "1"
        fourth_response = client.get("/something/2")
        assert fourth_response.status_code == HTTP_200_OK
        assert fourth_response.text == "2"


@pytest.mark.parametrize(
    "handler_path, request_path, expected_status_code",
    [
        ("/sub-path", "/", HTTP_404_NOT_FOUND),
        ("/sub/path", "/sub-path", HTTP_404_NOT_FOUND),
        ("/sub/path", "/sub", HTTP_404_NOT_FOUND),
        ("/sub/path/{path_param:int}", "/sub/path", HTTP_404_NOT_FOUND),
        ("/sub/path/{path_param:int}", "/sub/path/abcd", HTTP_404_NOT_FOUND),
        ("/sub/path/{path_param:uuid}", "/sub/path/100", HTTP_404_NOT_FOUND),
        ("/sub/path/{path_param:float}", "/sub/path/abcd", HTTP_404_NOT_FOUND),
    ],
)
def test_path_validation(handler_path: str, request_path: str, expected_status_code: int) -> None:
    @get(handler_path)
    def handler_fn(**kwargs: Any) -> None: ...

    with create_test_client(handler_fn) as client:
        response = client.get(request_path)
        assert response.status_code == expected_status_code


async def test_http_route_raises_for_unsupported_method(anyio_backend: str) -> None:
    @get()
    def my_get_handler() -> None:
        pass

    @post()
    def my_post_handler() -> None:
        pass

    with create_test_client(route_handlers=[my_get_handler, my_post_handler]) as client:
        response = client.delete("/")
        assert response.status_code == HTTP_405_METHOD_NOT_ALLOWED


def test_path_order() -> None:
    @get(path=["/something/{some_id:int}", "/"], media_type=MediaType.TEXT)
    def handler_fn(some_id: int = 1) -> str:
        return str(some_id)

    with create_test_client(handler_fn) as client:
        first_response = client.get("/something/5")
        assert first_response.status_code == HTTP_200_OK
        assert first_response.text == "5"
        second_response = client.get("/")
        assert second_response.status_code == HTTP_200_OK
        assert second_response.text == "1"


@pytest.mark.parametrize(
    "handler_path, request_path, expected_status_code, expected_param",
    [
        ("/name:str/{name:str}", "/name:str/test", HTTP_200_OK, "test"),
        ("/user/*/{name:str}", "/user/foo/bar", HTTP_404_NOT_FOUND, None),
        ("/user/*/{name:str}", "/user/*/bar", HTTP_200_OK, "bar"),
    ],
)
def test_special_chars(
    handler_path: str, request_path: str, expected_status_code: int, expected_param: Optional[str]
) -> None:
    @get(path=handler_path, media_type=MediaType.TEXT)
    def handler_fn(name: str) -> str:
        return name

    with create_test_client(handler_fn) as client:
        response = client.get(request_path)
        assert response.status_code == expected_status_code

        if response.status_code == HTTP_200_OK:
            assert response.text == expected_param


def test_no_404_where_list_route_has_handlers_and_child_route_has_path_param() -> None:
    # https://github.com/litestar-org/litestar/issues/816

    # the error condition requires the path to not be a plain route, hence the prefixed path parameters
    @get("/{a:str}/b")
    def get_list() -> List[str]:
        return ["ok"]

    @get("/{a:str}/b/{c:int}")
    def get_member() -> str:
        return "ok"

    with create_test_client(route_handlers=[get_list, get_member]) as client:
        resp = client.get("/scope/b")
        assert resp.status_code == 200
        assert resp.json() == ["ok"]


def test_support_of_different_branches() -> None:
    @get("/{foo:int}/foo")
    def foo_handler(foo: int) -> int:
        return foo

    @get("/{bar:str}/bar")
    def bar_handler(bar: str) -> str:
        return bar

    with create_test_client([foo_handler, bar_handler]) as client:
        response = client.get("1/foo")
        assert response.status_code == HTTP_200_OK

        response = client.get("a/bar")
        assert response.status_code == HTTP_200_OK


def test_support_for_path_type_parameters() -> None:
    @get(path="/{string_param:str}")
    def lower_handler(string_param: str) -> str:
        return string_param

    @get(path="/{string_param:str}/{path_param:path}")
    def upper_handler(string_param: str, path_param: Path) -> str:
        return string_param + str(path_param)

    with create_test_client([lower_handler, upper_handler]) as client:
        response = client.get("/abc")
        assert response.status_code == HTTP_200_OK

        response = client.get("/abc/a/b/c")
        assert response.status_code == HTTP_200_OK


def test_base_path_param_resolution() -> None:
    # https://github.com/litestar-org/litestar/issues/1830
    @get("/{name:str}")
    async def hello_world(name: str) -> str:
        return f"Hello, {name}!"

    with create_test_client(hello_world) as client:
        response = client.get("/jon")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Hello, jon!"

        response = client.get("/jon/bon")
        assert response.status_code == HTTP_404_NOT_FOUND

        response = client.get("/jon/bon/jovi")
        assert response.status_code == HTTP_404_NOT_FOUND


def test_base_path_param_resolution_2() -> None:
    # https://github.com/litestar-org/litestar/issues/1830#issuecomment-1642291149
    @get("/{name:str}")
    async def name_greeting(name: str) -> str:
        return f"Hello, {name}!"

    @get("/{age:int}")
    async def age_greeting(name: str, age: int) -> str:
        return f"Hello, {name}! {age} is a great age to be!"

    age_router = Router("/{name:str}/age", route_handlers=[age_greeting])
    name_router = Router("/name", route_handlers=[name_greeting, age_router])

    with create_test_client(name_router) as client:
        response = client.get("/name/jon")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Hello, jon!"

        response = client.get("/name/jon/age/42")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Hello, jon! 42 is a great age to be!"

        response = client.get("/name/jon/bon")
        assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "server_command",
    [
        pytest.param(["uvicorn", "app:app", "--port", "9999", "--root-path", "/test"], id="uvicorn"),
        pytest.param(["hypercorn", "app:app", "--bind", "127.0.0.1:9999", "--root-path", "/test"], id="hypercorn"),
        pytest.param(["daphne", "app:app", "--port", "9999", "--root-path", "/test"], id="daphne"),
    ],
)
@pytest.mark.xdist_group("live_server_test")
@pytest.mark.server_integration
def test_server_root_path_handling(
    tmp_path: Path, monkeypatch: MonkeyPatch, server_command: List[str], run_server: Callable[[str, List[str]], None]
) -> None:
    # https://github.com/litestar-org/litestar/issues/2998
    app = """
from litestar import Litestar, get, Request
from typing import List

@get("/handler")
async def handler(request: Request) -> List[str]:
    return [request.scope["path"], request.scope["root_path"]]

app = Litestar(route_handlers=[handler])
    """

    run_server(app, server_command)

    assert httpx.get("http://127.0.0.1:9999/handler").json() == ["/handler", "/test"]


@pytest.mark.parametrize(
    "server_command",
    [
        pytest.param(["uvicorn", "app:app", "--port", "9999", "--root-path", "/test"], id="uvicorn"),
        pytest.param(["hypercorn", "app:app", "--bind", "127.0.0.1:9999", "--root-path", "/test"], id="hypercorn"),
        pytest.param(["daphne", "app:app", "--port", "9999", "--root-path", "/test"], id="daphne"),
    ],
)
@pytest.mark.xdist_group("live_server_test")
@pytest.mark.server_integration
def test_server_root_path_handling_empty_path(
    tmp_path: Path, monkeypatch: MonkeyPatch, server_command: List[str], run_server: Callable[[str, List[str]], None]
) -> None:
    # https://github.com/litestar-org/litestar/issues/3041
    app = """
from pathlib import Path

from litestar import Litestar
from litestar.handlers import get
from typing import Optional

@get(path=["/", "/{path:path}"])
async def pathfinder(path: Optional[Path]) -> str:
    return str(path)

app = Litestar(route_handlers=[pathfinder], debug=True)
    """

    run_server(app, server_command)

    assert httpx.get("http://127.0.0.1:9999/").text == "None"
    assert httpx.get("http://127.0.0.1:9999/something").text == "/something"
