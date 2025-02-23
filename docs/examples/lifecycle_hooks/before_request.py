from typing import Optional

from litestar import Litestar, Request, get


async def before_request_handler(request: Request) -> Optional[dict[str, str]]:
    name = request.query_params["name"]
    if name == "Ben":
        return {"message": "These are not the bytes you are looking for"}
    request.state["message"] = f"Use the handler, {name}"
    return None


@get("/")
async def handler(request: Request, name: str) -> dict[str, str]:
    message: str = request.state["message"]
    return {"message": message}


app = Litestar(route_handlers=[handler], before_request=before_request_handler)

# run: /?name=Luke
# run: /?name=Ben
