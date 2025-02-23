from __future__ import annotations

from typing import Any

import pytest

from litestar import Controller, Router, delete, get, patch, post, put
from litestar.testing import create_test_client
from litestar.types import HTTPHandlerDecorator


@pytest.mark.parametrize(
    ("method", "decorator"),
    [
        ("GET", get),
        ("PUT", put),
        ("POST", post),
        ("PATCH", patch),
        ("DELETE", delete),
    ],
)
def test_websocket_signature_namespace(method: str, decorator: HTTPHandlerDecorator) -> None:
    class MyController(Controller):
        path = "/"
        signature_namespace = {"c": float}

        @decorator(path="/", signature_namespace={"d": list[str], "dict": dict}, status_code=200)
        async def simple_handler(
            self,
            a: a,  # type:ignore[name-defined]  # noqa: F821
            b: b,  # type:ignore[name-defined]  # noqa: F821
            c: c,  # type:ignore[name-defined]  # noqa: F821
            d: d,  # type:ignore[name-defined]  # noqa: F821
        ) -> dict[str, Any]:
            return {"a": a, "b": b, "c": c, "d": d}

    router = Router("/", route_handlers=[MyController], signature_namespace={"b": str})

    with create_test_client(route_handlers=[router], signature_namespace={"a": int}) as client:
        response = client.request(method=method, url="/?a=1&b=two&c=3.0&d=d")
        assert response.json() == {"a": 1, "b": "two", "c": 3.0, "d": ["d"]}
