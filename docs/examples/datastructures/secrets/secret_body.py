from dataclasses import dataclass

from litestar import post
from litestar.datastructures.secret_values import SecretString


@dataclass
class Sensitive:
    value: SecretString


@post(sync_to_thread=False)
def post_handler(data: Sensitive) -> Sensitive:
    return data
