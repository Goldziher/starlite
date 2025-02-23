from typing import Any

import litestar.status_codes
from litestar import Litestar, get


@get(
    "/resources",
    status_code=litestar.status_codes.HTTP_418_IM_A_TEAPOT,
    media_type="application/vnd.example.resource+json",
)
async def retrieve_resource() -> dict[str, Any]:
    return {
        "title": "Server thinks it is a teapot",
        "type": "Server delusion",
        "status": litestar.status_codes.HTTP_418_IM_A_TEAPOT,
    }


app = Litestar(route_handlers=[retrieve_resource])
