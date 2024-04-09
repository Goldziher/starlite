from typing import Any, Dict

import litestar.status_codes
from litestar import Litestar, get


@get("/resources", status_code=litestar.status_codes.HTTP_418_IM_A_TEAPOT, media_type="application/problem+json")
async def retrieve_resource() -> Dict[str, Any]:
    return {
        "title": "Server thinks it is a teapot",
        "type": "Server delusion",
        "status": litestar.status_codes.HTTP_418_IM_A_TEAPOT,
    }


app = Litestar(route_handlers=[retrieve_resource])
