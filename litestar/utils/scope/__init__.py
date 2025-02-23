from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.serialization import get_serializer

if TYPE_CHECKING:
    from litestar.types import Scope, Serializer

__all__ = ("get_serializer_from_scope",)


def get_serializer_from_scope(scope: Scope) -> Serializer:
    """Return a serializer given a scope object.

    Args:
        scope: The ASGI connection scope.

    Returns:
        A serializer function
    """
    route_handler = scope["route_handler"]
    app = scope["litestar_app"]

    type_encoders = route_handler.type_encoders if hasattr(route_handler, "type_encoders") else app.type_encoders or {}

    if response_class := (
        route_handler.response_class  # pyright: ignore
        if hasattr(route_handler, "response_class")
        else app.response_class
    ):
        type_encoders = {**type_encoders, **(response_class.type_encoders or {})}

    return get_serializer(type_encoders)
