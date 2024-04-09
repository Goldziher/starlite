from os import urandom

from litestar import Litestar
from litestar.middleware.session.client_side import CookieBackendConfig

session_config = CookieBackendConfig(secret=urandom(16))  # type: ignore

app = Litestar(middleware=[session_config.middleware])
