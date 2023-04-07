from litestar import Starlite, websocket_listener


@websocket_listener("/", receive_mode="text")
async def handler(data: str) -> str:
    return data


app = Starlite([handler])
