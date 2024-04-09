from uuid import uuid4

from litestar import Controller, HttpMethod, Litestar, Response, Router, get
from litestar.datastructures import Cookie
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


def test_response_cookies() -> None:
    router_first = Cookie(key="second", value="1")
    router_second = Cookie(key="third", value="2")
    controller_first = Cookie(key="first", value="3")
    controller_second = Cookie(key="second", value="4")
    app_first = Cookie(key="first", value="5")
    app_second = Cookie(key="fourth", value="6")
    local_first = Cookie(key="first", value="7")

    test_path = "/test"

    class MyController(Controller):
        path = test_path
        response_cookies = [controller_first, controller_second]

        @get(
            path="/{path_param:str}",
            response_cookies=[local_first],
        )
        def test_method(self) -> None:
            pass

    first_router = Router(path="/users", response_cookies=[router_first, router_second], route_handlers=[MyController])

    second_router = Router(path="/external", response_cookies=[Cookie(key="external", value="nope")], route_handlers=[])

    app = Litestar(
        openapi_config=None,
        response_cookies=[app_first, app_second],
        route_handlers=[first_router, second_router],
    )
    route_handler, _ = app.routes[0].route_handler_map[HttpMethod.GET]  # type: ignore[union-attr]
    response_cookies = {cookie.key: cookie.value for cookie in route_handler.resolve_response_cookies()}
    assert response_cookies["first"] == local_first.value
    assert response_cookies["second"] == controller_second.value
    assert response_cookies["third"] == router_second.value
    assert response_cookies["fourth"] == app_second.value
    assert "external" not in response_cookies


def test_response_cookies_mapping() -> None:
    @get(response_cookies={"foo": "bar"})
    def handler_one() -> None:
        pass

    @get(response_cookies=[Cookie(key="foo", value="bar")])
    def handler_two() -> None:
        pass

    assert handler_one.resolve_response_cookies() == handler_two.resolve_response_cookies()


def test_response_cookies_mapping_unresolved() -> None:
    # this should never happen, as there's no way to create this situation which type-checks.
    # we test for it nevertheless

    @get()
    def handler_one() -> None:
        pass

    handler_one.response_cookies = {"foo": "bar"}  # type: ignore[assignment]

    assert handler_one.resolve_response_cookies() == frozenset([Cookie(key="foo", value="bar")])


def test_response_cookie_rendering() -> None:
    @get(
        "/",
        response_cookies=[Cookie(key="test", value="123")],
    )
    def test_method() -> None:
        return None

    with create_test_client(test_method) as client:
        response = client.get("/")
        assert response.headers["Set-Cookie"] == "test=123; Path=/; SameSite=lax"


def test_response_cookie_documentation_only_not_rendering() -> None:
    @get(
        "/",
        response_cookies=[
            Cookie(
                key="my-cookie",
                description="my-cookie documentations",
                documentation_only=True,
            )
        ],
    )
    def test_method() -> None:
        return None

    with create_test_client(test_method) as client:
        response = client.get("/")
        assert "Set-Cookie" not in response.headers


def test_response_cookie_documentation_only_not_producing_second_header() -> None:
    # https://github.com/litestar-org/litestar/issues/870
    def after_request(response: Response) -> Response:
        response.set_cookie("my-cookie", "123")
        return response

    @get(
        "/",
        response_cookies=[
            Cookie(
                key="my-cookie",
                description="my-cookie documentations",
                documentation_only=True,
            )
        ],
    )
    def test_method() -> None:
        return None

    with create_test_client(test_method, after_request=after_request) as client:
        response = client.get("/")
        assert response.headers["Set-Cookie"] == "my-cookie=123; Path=/; SameSite=lax"
        assert len(response.headers.get_list("Set-Cookie")) == 1


def test_response_cookie_is_always_set() -> None:
    # https://github.com/litestar-org/litestar/issues/888
    @get(path="/set-cookie")
    def set_cookie_handler() -> Response[None]:
        return Response(
            content=None,
            cookies=[
                Cookie(
                    key="test",
                    value=str(uuid4()),
                    expires=10,
                )
            ],
        )

    with create_test_client([set_cookie_handler]) as client:
        response = client.get("/set-cookie")
        assert response.status_code == HTTP_200_OK
        assert response.cookies.get("test")
        cookie = response.cookies.get("test")
        client.cookies.clear()
        response = client.get("/set-cookie")
        assert response.status_code == HTTP_200_OK
        assert response.cookies.get("test")
        assert cookie != response.cookies.get("test")
