from os import environ

from my_app.guards import secret_token_guard

from litestar import get


@get(path="/secret", guards=[secret_token_guard], opt={"secret": environ.get("SECRET")})
def secret_endpoint() -> None: ...
