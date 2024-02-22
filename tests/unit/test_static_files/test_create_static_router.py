from typing import Any

from litestar import Litestar, Request, Response, Router
from litestar.connection import ASGIConnection
from litestar.datastructures import CacheControlHeader
from litestar.exceptions import ValidationException
from litestar.handlers import BaseRouteHandler
from litestar.static_files import create_static_files_router


def test_route_reverse() -> None:
    app = Litestar(
        route_handlers=[create_static_files_router(path="/static", directories=["something"], name="static")]
    )

    assert app.route_reverse("static", file_path="foo.py") == "/static/foo.py"


def test_pass_options() -> None:
    def guard(connection: ASGIConnection, handler: BaseRouteHandler) -> None:
        pass

    def handle(request: Request, exception: Any) -> Response:
        return Response(b"")

    async def after_request(response: Response) -> Response:
        return Response(b"")

    async def after_response(request: Request) -> None:
        pass

    async def before_request(request: Request) -> Any:
        pass

    exception_handlers = {ValidationException: handle}
    opts = {"foo": "bar"}
    cache_control = CacheControlHeader()
    security = [{"foo": ["bar"]}]
    tags = ["static", "random"]

    router = create_static_files_router(
        path="/",
        directories=["something"],
        guards=[guard],
        exception_handlers=exception_handlers,  # type: ignore[arg-type]
        opt=opts,
        after_request=after_request,
        after_response=after_response,
        before_request=before_request,
        cache_control=cache_control,
        include_in_schema=False,
        security=security,
        tags=tags,
    )

    assert router.guards == [guard]
    assert router.exception_handlers == exception_handlers
    assert router.opt == opts
    assert router.after_request is after_request
    assert router.after_response is after_response
    assert router.before_request is before_request
    assert router.cache_control is cache_control
    assert router.include_in_schema is False
    assert router.security == security
    assert router.tags == tags


def test_custom_router_class() -> None:
    class MyRouter(Router):
        pass

    router = create_static_files_router("/", directories=["some"], router_class=MyRouter)
    assert isinstance(router, MyRouter)
