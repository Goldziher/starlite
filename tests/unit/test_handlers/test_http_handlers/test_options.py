import pytest

from litestar import Router, get
from litestar.testing import create_test_client


@pytest.mark.xfail(reason="broken behaviour that never really worked")
def test_option_handler_inherits_layer_config() -> None:
    # Currently broken. The reason this cannot work reliably is that when auto-creating
    # OPTIONS handlers, we *assume* that it should inherit the configuration of
    # path-adjacent route handlers, e.g. if a route handler is defined on '/', and
    # registered on a router with the path '/one', it would receive the configuration
    # from that router. However, since it is possible to have multiple handlers per
    # path, which can also be registered with different routers, we would still only
    # create one 'OPTIONS' handler for each path, even if multiple routers exist with
    # handlers for that path. In this case, it is unclear which configuration the
    # 'OPTIONS' handler should receive
    @get("/")
    def handler() -> None:
        return None

    router = Router(path="/router", route_handlers=[handler], response_headers={"router": "router"})

    with create_test_client(route_handlers=[handler, router], response_headers={"app": "app"}) as client:
        res = client.options("/")
        assert res.headers.get("app") == "app"
        assert res.headers.get("router") == "router"
