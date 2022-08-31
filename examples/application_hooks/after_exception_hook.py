import logging
from typing import TYPE_CHECKING

from starlette.status import HTTP_400_BAD_REQUEST

from starlite import HTTPException, Starlite, get

logger = logging.getLogger()

if TYPE_CHECKING:
    from starlite.datastructures import State
    from starlite.types import Scope


@get("/some-path")
def my_handler() -> None:
    """Route handler that raises an exception."""
    raise HTTPException(detail="bad request", status_code=HTTP_400_BAD_REQUEST)


async def after_exception_handler(exc: Exception, scope: "Scope", state: "State") -> None:
    """Hook function that will be invoked after each exception."""
    if not hasattr(state, "error_count"):
        state.error_count = 1
    else:
        state.error_count += 1

    logger.info(
        "an exception of type %s has occurred for requested path %s and the application error count is %d.",
        type(exc).__name__,
        scope["path"],
        state.error_count,
    )


app = Starlite([my_handler], after_exception=after_exception_handler)
