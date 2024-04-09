from litestar import WebSocket, websocket
from litestar.params import Parameter
from litestar.testing import create_test_client


def test_handle_websocket_params_parsing() -> None:
    @websocket(path="/{socket_id:int}")
    async def websocket_handler(
        socket: WebSocket,
        headers: dict,
        query: dict,
        cookies: dict,
        socket_id: int,
        qp: int,
        hp: str = Parameter(header="some-header"),
    ) -> None:
        assert socket_id
        assert headers
        assert query
        assert cookies
        assert qp
        assert hp
        await socket.accept()
        data = await socket.receive_json()
        assert data
        await socket.send_json({"data": "123"})
        await socket.close()

    client = create_test_client(route_handlers=websocket_handler)

    # Set cookies on the client to avoid warnings about per-request cookies.
    client.cookies = {"cookie": "yum"}  # type: ignore[assignment]

    with client.websocket_connect("/1?qp=1", headers={"some-header": "abc"}) as ws:
        ws.send_json({"data": "123"})
        data = ws.receive_json()
        assert data
