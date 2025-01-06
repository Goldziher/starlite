from typing import Any, Dict

import pytest

from litestar import Litestar, Request, get
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.testing import AsyncTestClient

session_config = ServerSideSessionConfig()


@get(path="/test", sync_to_thread=False)
def get_session_data(request: Request) -> Dict[str, Any]:
    return request.session


app = Litestar(route_handlers=[get_session_data], middleware=[session_config.middleware], debug=True)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "anyio_backend",
    [
        pytest.param("asyncio"),
        pytest.param("trio", marks=pytest.mark.xfail(reason="Known issue with trio backend", strict=False)),
    ],
)
async def test_get_session_data() -> None:
    async with AsyncTestClient(app=app, session_config=session_config) as client:
        await client.set_session_data({"foo": "bar"})
        res = await client.get("/test")
        assert res.json() == {"foo": "bar"}
