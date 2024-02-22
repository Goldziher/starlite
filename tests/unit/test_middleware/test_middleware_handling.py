import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable, List, cast

import pytest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from litestar import Controller, Request, Response, Router, get, post
from litestar.enums import ScopeType
from litestar.middleware import DefineMiddleware, MiddlewareProtocol
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from typing import Type

    from _pytest.logging import LogCaptureFixture

    from litestar.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class MiddlewareProtocolRequestLoggingMiddleware(MiddlewareProtocol):
    def __init__(self, app: "ASGIApp", kwarg: str = "") -> None:
        self.app = app
        self.kwarg = kwarg

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["type"] == ScopeType.HTTP:
            request = Request[Any, Any, Any](scope=scope, receive=receive)
            body = await request.json()
            logger.info(f"test logging: {request.method}, {request.url}, {body}")
        await self.app(scope, receive, send)


class BaseMiddlewareRequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:  # type: ignore
        logging.getLogger(__name__).info("%s - %s", request.method, request.url)
        return await call_next(request)  # type: ignore


class MiddlewareWithArgsAndKwargs(BaseHTTPMiddleware):
    def __init__(self, arg: int = 0, *, app: Any, kwarg: str) -> None:
        super().__init__(app)
        self.arg = arg
        self.kwarg = kwarg

    async def dispatch(  # type: ignore
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        ...


@pytest.mark.parametrize(
    "middleware",
    [
        BaseMiddlewareRequestLoggingMiddleware,
        # Middleware(MiddlewareWithArgsAndKwargs, kwarg="123Jeronimo"),  # pyright: ignore[reportGeneralTypeIssues] # noqa: ERA001
        # Middleware(MiddlewareProtocolRequestLoggingMiddleware, kwarg="123Jeronimo"),  # type: ignore[arg-type] # pyright: ignore[reportGeneralTypeIssues] # noqa: ERA001
        DefineMiddleware(MiddlewareWithArgsAndKwargs, 1, kwarg="123Jeronimo"),  # type: ignore[arg-type]
        DefineMiddleware(MiddlewareProtocolRequestLoggingMiddleware, kwarg="123Jeronimo"),
    ],
)
def test_custom_middleware_processing(middleware: Any) -> None:
    @get(path="/")
    def handler() -> None:
        ...

    with create_test_client(route_handlers=[handler], middleware=[middleware]) as client:
        app = client.app
        assert app.middleware == [middleware]

        unpacked_middleware = []
        cur = client.app.asgi_router.root_route_map_node.children["/"].asgi_handlers["GET"][0]
        while hasattr(cur, "app"):
            unpacked_middleware.append(cur)
            cur = cast("ASGIApp", cur.app)  # pyright: ignore
        unpacked_middleware.append(cur)
        assert len(unpacked_middleware) == 4

        middleware_instance = unpacked_middleware[1]

        assert isinstance(
            middleware_instance,
            (
                MiddlewareProtocolRequestLoggingMiddleware,
                BaseMiddlewareRequestLoggingMiddleware,
                MiddlewareWithArgsAndKwargs,
            ),
        )
        if isinstance(middleware_instance, (MiddlewareProtocolRequestLoggingMiddleware, MiddlewareWithArgsAndKwargs)):
            assert middleware_instance.kwarg == "123Jeronimo"
        if isinstance(middleware, DefineMiddleware) and isinstance(middleware_instance, MiddlewareWithArgsAndKwargs):
            assert middleware_instance.arg == 1


def test_request_body_logging_middleware(caplog: "LogCaptureFixture") -> None:
    @dataclass
    class JSONRequest:
        name: str
        age: int
        programmer: bool

    @post(path="/")
    def post_handler(data: JSONRequest) -> JSONRequest:
        return data

    with caplog.at_level(logging.INFO):
        client = create_test_client(
            route_handlers=[post_handler], middleware=[MiddlewareProtocolRequestLoggingMiddleware]
        )
        response = client.post("/", json={"name": "moishe zuchmir", "age": 40, "programmer": True})
        assert response.status_code == 201
        assert "test logging" in caplog.text


def test_middleware_call_order() -> None:
    """Test that middlewares are called in the order they have been passed."""

    results: List[int] = []

    def create_test_middleware(middleware_id: int) -> "Type[MiddlewareProtocol]":
        class TestMiddleware(MiddlewareProtocol):
            def __init__(self, app: "ASGIApp") -> None:
                self.app = app

            async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
                results.append(middleware_id)
                await self.app(scope, receive, send)

        return TestMiddleware

    class MyController(Controller):
        path = "/controller"
        middleware = [create_test_middleware(4), create_test_middleware(5)]

        @get("/handler", middleware=[create_test_middleware(6), create_test_middleware(7)])
        def my_handler(self) -> None:
            return None

    router = Router(
        path="/router", route_handlers=[MyController], middleware=[create_test_middleware(2), create_test_middleware(3)]
    )

    with create_test_client(
        route_handlers=[router],
        middleware=[create_test_middleware(0), create_test_middleware(1)],
    ) as client:
        client.get("/router/controller/handler")

        assert results == [0, 1, 2, 3, 4, 5, 6, 7]
