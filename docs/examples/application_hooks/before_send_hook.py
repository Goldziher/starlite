from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Litestar, get
from litestar.datastructures import MutableScopeHeaders

if TYPE_CHECKING:
    from litestar.types import Message, Scope


@get("/test", sync_to_thread=False)
def handler() -> dict[str, str]:
    """Example Handler function."""
    return {"key": "value"}


async def before_send_hook_handler(message: Message, scope: Scope) -> None:
    """The function will be called on each ASGI message.

    We therefore ensure it runs only on the message start event.
    """
    if message["type"] == "http.response.start":
        headers = MutableScopeHeaders.from_message(message=message)
        headers["My Header"] = Litestar.from_scope(scope).state.message


def on_startup(app: Litestar) -> None:
    """A function that will populate the app state before any requests are received."""
    app.state.message = "value injected during send"


app = Litestar(route_handlers=[handler], on_startup=[on_startup], before_send=[before_send_hook_handler])
