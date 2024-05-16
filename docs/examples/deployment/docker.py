"""Minimal Litestar application."""

from asyncio import sleep
from typing import Any, Dict

from litestar import Litestar, get


@get("/")
async def async_hello_world() -> Dict[str, Any]:
    """Route Handler that outputs hello world."""
    await sleep(0.1)
    return {"hello": "world"}


@get("/sync", sync_to_thread=False)
def sync_hello_world() -> Dict[str, Any]:
    """Route Handler that outputs hello world."""
    return {"hello": "world"}


app = Litestar(route_handlers=[sync_hello_world, async_hello_world])
