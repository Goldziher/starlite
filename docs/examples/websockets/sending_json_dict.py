from litestar import Litestar, websocket_listener


@websocket_listener("/")
async def handler(data: str) -> dict[str, str]:
    return {"message": data}


app = Litestar([handler])
