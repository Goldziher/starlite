import inspect
from functools import wraps
from typing import TYPE_CHECKING, Callable, List, Literal, Optional, TypeVar
from warnings import warn

from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from starlite.utils.sync import AsyncCallable

T = TypeVar("T")
P = ParamSpec("P")
DeprecatedKind = Literal["function", "method", "attribute", "property", "class", "parameter"]


def warn_deprecation(
    version: str,
    deprecated_name: str,
    kind: DeprecatedKind,
    *,
    removal_in: Optional[str] = None,
    alternative: Optional[str] = None,
    info: Optional[str] = None,
    pending: bool = False,
) -> None:
    """Warn about a call to a (soon to be) deprecated function.

    Args:
        version: Starlite version where the deprecation will occur
        deprecated_name: Name of the deprecated function
        removal_in: Starlite version where the deprecated function will be removed
        alternative: Name of a function that should be used instead
        info: Additional information
        pending: Use `PendingDeprecationWarning` instead of `DeprecationWarning`
        kind: Type of the deprecated thing
    """
    parts = []
    access_type = "Call to" if kind in {"function", "method"} else "Use of"
    removal_in = removal_in or "the next major version"
    if pending:
        parts.append(f"{access_type} {kind} awaiting deprecation {deprecated_name!r}")
    else:
        parts.append(f"{access_type} deprecated {kind} {deprecated_name!r}")
    parts.append(f"Deprecated in starlite {version}")
    if removal_in:
        parts.append(f"This {kind} will be removed in {removal_in}")
    if alternative:
        parts.append(f"Use {alternative!r} instead")
    if info:
        parts.append(info)

    text = ". ".join(parts)
    warning_class = PendingDeprecationWarning if pending else DeprecationWarning

    warn(text, warning_class)


def deprecated(
    version: str,
    *,
    removal_in: Optional[str] = None,
    alternative: Optional[str] = None,
    info: Optional[str] = None,
    pending: bool = False,
    kind: Optional[Literal["function", "method", "property"]] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Create a decorator wrapping a function, method or property with a warning call about a (pending) deprecation.

    Args:
        version: Starlite version where the deprecation will occur
        removal_in: Starlite version where the deprecated function will be removed
        alternative: Name of a function that should be used instead
        info: Additional information
        pending: Use `PendingDeprecationWarning` instead of `DeprecationWarning`
        kind: Type of the deprecated callable. If `None`, will use `inspect` to figure
            out if it's a function or method

    Returns:
        A decorator wrapping the function call with a warning
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            warn_deprecation(
                version=version,
                deprecated_name=func.__name__,
                info=info,
                alternative=alternative,
                pending=pending,
                removal_in=removal_in,
                kind=kind or ("method" if inspect.ismethod(func) else "function"),
            )
            return func(*args, **kwargs)

        return wrapped

    return decorator


def deprecate_two_arg_before_send_hook_handlers(handlers: List["AsyncCallable"]) -> List["AsyncCallable"]:
    """Emit a deprecation warning if any of `handlers` have two argument signature.

    Args:
        handlers: Before send hook handlers registered on the application.

    Returns:
        The handlers, unmodified.
    """
    if any(handler.num_expected_args == 2 for handler in handlers):
        warn_deprecation(
            version="1.40",
            deprecated_name="Before send hook handlers with two args.",
            removal_in="1.50",
            alternative="Before send hook handlers with three args.",
            info="See 3 argument signature documented at "
            "https://starlite-api.github.io/starlite/reference/types/1-callable-types/#starlite.types.BeforeMessageSendHookHandler",
            kind="parameter",
        )
    return handlers
