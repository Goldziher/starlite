from litestar import Litestar
from litestar.config.allowed_hosts import AllowedHostsConfig

app = Litestar(
    route_handlers=[...],
    allowed_hosts=AllowedHostsConfig(allowed_hosts=["*.example.com", "www.wikipedia.org"]),
)
