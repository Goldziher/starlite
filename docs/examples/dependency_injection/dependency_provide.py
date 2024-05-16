from random import randint

from litestar import get
from litestar.di import Provide


def my_dependency() -> int:
    return randint(1, 10)


@get(
    "/some-path",
    dependencies={
        "my_dep": Provide(
            my_dependency,
        )
    },
)
def my_handler(my_dep: int) -> None: ...
