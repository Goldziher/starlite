from random import randint

from litestar import Litestar, get
from litestar.di import Provide


def first_dependency() -> int:
    return randint(1, 10)


def second_dependency(injected_integer: int) -> bool:
    return injected_integer % 2 == 0


@get("/true-or-false")
def true_or_false_handler(injected_bool: bool) -> str:
    return "its true!" if injected_bool else "nope, its false..."


app = Litestar(
    route_handlers=[true_or_false_handler],
    dependencies={
        "injected_integer": Provide(first_dependency),
        "injected_bool": Provide(second_dependency),
    },
)
