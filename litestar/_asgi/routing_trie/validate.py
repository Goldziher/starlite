from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING

from litestar.exceptions import ImproperlyConfiguredException

__all__ = ("validate_node",)


if TYPE_CHECKING:
    from litestar._asgi.routing_trie.types import RouteTrieNode


def validate_node(node: RouteTrieNode) -> None:
    """Recursively traverses the trie from the given node upwards.

    Args:
        node: A trie node.

    Raises:
        ImproperlyConfiguredException

    Returns:
        None
    """
    if node.is_asgi and bool(set(node.asgi_handlers).difference({"asgi"})):
        msg = "ASGI handlers must have a unique path not shared by other route handlers."
        raise ImproperlyConfiguredException(msg)

    if (
        node.is_mount
        and node.children
        and any(
            chain.from_iterable(
                list(child.path_parameters.values())
                if isinstance(child.path_parameters, dict)
                else child.path_parameters
                for child in node.children.values()
            ),
        )
    ):
        msg = "Path parameters are not allowed under a static or mount route."
        raise ImproperlyConfiguredException(msg)

    for child in node.children.values():
        validate_node(node=child)
