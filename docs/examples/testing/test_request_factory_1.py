from litestar import Request
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler


def secret_token_guard(request: Request, route_handler: BaseRouteHandler) -> None:
    if route_handler.opt.get("secret") and not request.headers.get("Secret-Header", "") == route_handler.opt["secret"]:
        raise NotAuthorizedException()
