import re
from typing import TYPE_CHECKING, Optional, Pattern, Set

from starlette.datastructures import URL

from starlite.datastructures import MutableScopeHeaders
from starlite.middleware.base import AbstractMiddleware
from starlite.response import RedirectResponse, Response
from starlite.status_codes import HTTP_400_BAD_REQUEST

if TYPE_CHECKING:
    from starlite.config.allowed_hosts import AllowedHostsConfig
    from starlite.types import ASGIApp, Receive, Scope, Send


class AllowedHostsMiddleware(AbstractMiddleware):
    def __init__(self, app: "ASGIApp", config: "AllowedHostsConfig"):
        """Middleware that ensures the host of a request originated in a
        trusted host.

        Args:
            app: The 'next' ASGI app to call.
            config: An instance of AllowedHostsConfig.
        """

        super().__init__(app=app, exclude=config.exclude, exclude_opt_key=config.exclude_opt_key, scopes=config.scopes)

        self.allowed_hosts_regex: Optional[Pattern] = None
        self.redirect_domains: Optional[Pattern] = None

        if any(host == "*" for host in config.allowed_hosts):
            return

        allowed_hosts: Set[str] = {
            rf".*\.{host.removeprefix('*.')}$" if host.startswith("*.") else host for host in config.allowed_hosts
        }

        self.allowed_hosts_regex = re.compile("|".join(sorted(allowed_hosts)))

        if config.www_redirect:
            redirect_domains: Set[str] = {rf"(?:www\.|){host}" for host in config.allowed_hosts if "*" not in host}
            if redirect_domains:
                self.redirect_domains = re.compile("|".join(sorted(redirect_domains)))

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        if self.allowed_hosts_regex is None:
            await self.app(scope, receive, send)
            return

        headers = MutableScopeHeaders(scope=scope)
        host = headers.get("host", headers.get("x-forwarded-host", "")).split(":")[0]

        if host:
            if self.allowed_hosts_regex.findall(host):
                await self.app(scope, receive, send)
                return

            if self.redirect_domains is not None and self.redirect_domains.findall(host):
                url = URL(scope=scope)  # type: ignore
                redirect_url = url.replace(netloc="www." + url.netloc)
                await RedirectResponse(url=str(redirect_url))(scope, receive, send)
                return

        await Response(content={"message": "invalid host header"}, status_code=HTTP_400_BAD_REQUEST)(
            scope, receive, send
        )
