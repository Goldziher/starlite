from __future__ import annotations

import re
from re import Pattern
from typing import TYPE_CHECKING

from litestar.exceptions import ImproperlyConfiguredException

__all__ = ("build_exclude_path_pattern", "should_bypass_middleware")

from litestar.utils.warnings import warn_middleware_excluded_on_all_routes

if TYPE_CHECKING:
    from collections.abc import Sequence

    from litestar.types import Method, Scope, Scopes


def build_exclude_path_pattern(
    *,
    exclude: str | list[str] | None = None,
    middleware_cls: type | None = None,
) -> Pattern | None:
    """Build single path pattern from list of patterns to opt-out from middleware processing.

    Args:
        exclude: A pattern or a list of patterns.
        middleware_cls: Middleware class this is being called from - used for creating
            more informative warnings

    Returns:
        An optional pattern to match against scope["path"] to opt-out from middleware processing.
    """
    if exclude is None:
        return None

    try:
        pattern = re.compile("|".join(exclude)) if isinstance(exclude, list) else re.compile(exclude)
        if pattern.match("/") and pattern.match("/982c7064-6ac7-44b7-9be5-07a2ff6d8a92"):
            # match a UUID to ensure that it matches paths greedily and not just a literal /
            warn_middleware_excluded_on_all_routes(pattern, middleware_cls=middleware_cls)
        return pattern

    except re.error as e:  # pragma: no cover
        raise ImproperlyConfiguredException(
            "Unable to compile exclude patterns for middleware. Please make sure you passed a valid regular expression."
        ) from e


def should_bypass_middleware(
    *,
    exclude_http_methods: Sequence[Method] | None = None,
    exclude_opt_key: str | None = None,
    exclude_path_pattern: Pattern | None = None,
    scope: Scope,
    scopes: Scopes,
) -> bool:
    """Determine weather a middleware should be bypassed.

    Args:
        exclude_http_methods: A sequence of http methods that do not require authentication.
        exclude_opt_key: Key in ``opt`` with which a route handler can "opt-out" of a middleware.
        exclude_path_pattern: If this pattern matches scope["path"], the middleware should be bypassed.
        scope: The ASGI scope.
        scopes: A set with the ASGI scope types that are supported by the middleware.

    Returns:
        A boolean indicating if a middleware should be bypassed
    """
    if scope["type"] not in scopes:
        return True

    if exclude_opt_key and scope["route_handler"].opt.get(exclude_opt_key):
        return True

    if exclude_http_methods and scope.get("method") in exclude_http_methods:
        return True

    return bool(
        exclude_path_pattern
        and exclude_path_pattern.findall(
            scope["raw_path"].decode() if getattr(scope.get("route_handler", {}), "is_mount", False) else scope["path"]
        )
    )
