from typing import TYPE_CHECKING

import pytest

from litestar import Litestar, asgi
from litestar.exceptions import ImproperlyConfiguredException
from litestar.routes import ASGIRoute
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from litestar.types import Receive, Scope, Send


def test_asgi_handler_validation() -> None:
    async def fn_without_scope_arg(receive: "Receive", send: "Send") -> None:
        pass

    with pytest.raises(ImproperlyConfiguredException):
        handler = asgi(path="/")(fn_without_scope_arg)
        handler.on_registration(ASGIRoute(path="/", route_handler=handler), app=Litestar())

    async def fn_without_receive_arg(scope: "Scope", send: "Send") -> None:
        pass

    with pytest.raises(ImproperlyConfiguredException):
        handler = asgi(path="/")(fn_without_receive_arg)
        handler.on_registration(ASGIRoute(path="/", route_handler=handler), app=Litestar())

    async def fn_without_send_arg(scope: "Scope", receive: "Receive") -> None:
        pass

    with pytest.raises(ImproperlyConfiguredException):
        handler = asgi(path="/")(fn_without_send_arg)
        handler.on_registration(ASGIRoute(path="/", route_handler=handler), app=Litestar())

    async def fn_with_return_annotation(scope: "Scope", receive: "Receive", send: "Send") -> dict:
        return {}

    with pytest.raises(ImproperlyConfiguredException):
        handler = asgi(path="/")(fn_with_return_annotation)
        handler.on_registration(ASGIRoute(path="/", route_handler=handler), app=Litestar())

    asgi_handler_with_no_fn = asgi(path="/")

    with pytest.raises(ImproperlyConfiguredException):
        create_test_client(route_handlers=asgi_handler_with_no_fn)

    def sync_fn(scope: "Scope", receive: "Receive", send: "Send") -> None:
        return None

    with pytest.raises(ImproperlyConfiguredException):
        handler = asgi(path="/")(sync_fn)  # type: ignore[arg-type]
        handler.on_registration(ASGIRoute(path="/", route_handler=handler), app=Litestar())
