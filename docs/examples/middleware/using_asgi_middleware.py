import anyio

from litestar import Litestar, get
from litestar.enums import ScopeType
from litestar.exceptions import ClientException
from litestar.middleware import ASGIMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send


class TimeoutMiddleware(ASGIMiddleware):
    # we can configure some things on the class level here, related to when our
    # middleware should be applied.

    # if the requests' 'scope["type"]' is not "http", the middleware will be skipped
    scopes = (ScopeType.HTTP,)

    # if the handler for a request has set an opt of 'no_timeout=True', the middleware
    # will be skipped
    exclude_opt_key = "no_timeout"

    # the base class does not define an '__init__' method, so we're free to overwrite
    # this, which we're making use of to add some configuration
    def __init__(
        self,
        timeout: float,
        exclude_path_pattern: str | tuple[str, ...] | None = None,
    ) -> None:
        self.timeout = timeout

        # we can also dynamically configure the options provided by the base class on
        # the instance level
        self.exclude_path_pattern = exclude_path_pattern

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        try:
            with anyio.fail_after(self.timeout):
                # call the next app in the chain
                await next_app(scope, receive, send)
        except TimeoutError:
            # if the request has timed out, raise an exception. since the whole
            # application is wrapped in an exception handling middleware, it will
            # transform this exception into a response for us
            raise ClientException(status_code=408) from None


@get("/", no_timeout=True)
async def handler_with_opt_skip() -> None:
    pass


@get("/not-this-path")
async def handler_with_path_skip() -> None:
    pass


app = Litestar(
    route_handlers=[
        handler_with_opt_skip,
        handler_with_path_skip,
    ],
    middleware=[TimeoutMiddleware(timeout=5)],
)
