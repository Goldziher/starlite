from datetime import datetime, timedelta
from typing import Any

from litestar import Litestar, get


@get("/", sync_to_thread=False)
def index(date: datetime, number: int, floating_number: float, strings: list[str]) -> dict[str, Any]:
    return {
        "datetime": date + timedelta(days=1),
        "int": number,
        "float": floating_number,
        "list": strings,
    }


app = Litestar(route_handlers=[index])


# run: /?date=2022-11-28T13:22:06.916540&floating_number=0.1&number=42&strings=1&strings=2
