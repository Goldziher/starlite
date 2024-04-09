from typing import Any, Dict

from litestar import Litestar, Request, get
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.testing import TestClient

session_config = ServerSideSessionConfig()


@get(path="/test", sync_to_thread=False)
def get_session_data(request: Request) -> Dict[str, Any]:
    return request.session


app = Litestar(route_handlers=[get_session_data], middleware=[session_config.middleware])


def test_get_session_data() -> None:
    with TestClient(app=app, session_config=session_config) as client:
        client.set_session_data({"foo": "bar"})
        assert client.get("/test").json() == {"foo": "bar"}
