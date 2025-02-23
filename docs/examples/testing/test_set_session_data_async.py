from typing import Any

from litestar import Litestar, Request, get
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.testing import AsyncTestClient

session_config = ServerSideSessionConfig()


@get(path="/test", sync_to_thread=False)
def get_session_data(request: Request) -> dict[str, Any]:
    return request.session


app = Litestar(route_handlers=[get_session_data], middleware=[session_config.middleware], debug=True)


async def test_get_session_data() -> None:
    async with AsyncTestClient(app=app, session_config=session_config) as client:
        await client.set_session_data({"foo": "bar"})
        res = await client.get("/test")
        assert res.json() == {"foo": "bar"}
