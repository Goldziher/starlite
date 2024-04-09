from __future__ import annotations

from dataclasses import dataclass
from secrets import compare_digest

from typing_extensions import Annotated

from litestar import get
from litestar.datastructures.secret_values import SecretString
from litestar.exceptions import NotAuthorizedException
from litestar.params import Parameter

SECRET_VALUE = "super-secret"  # An example secret value - this should be stored securely in production.


@dataclass
class Sensitive:
    value: str


@get(sync_to_thread=False)
def get_handler(secret: Annotated[SecretString, Parameter(header="x-secret")]) -> Sensitive:
    if not compare_digest(secret.get_secret(), SECRET_VALUE):
        raise NotAuthorizedException
    return Sensitive(value="sensitive data")
