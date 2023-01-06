# Using Dependencies in Dependencies

You can inject dependencies into other dependencies - exactly like you would into regular functions.

```python
from starlite import Starlite, Provide, get
from random import randint


def first_dependency() -> int:
    return randint(1, 10)


def second_dependency(injected_integer: int) -> bool:
    return injected_integer % 2 == 0


@get("/true-or-false")
def true_or_false_handler(injected_bool: bool) -> str:
    return "its true!" if injected_bool else "nope, its false..."


app = Starlite(
    route_handlers=[true_or_false_handler],
    dependencies={
        "injected_integer": Provide(first_dependency),
        "injected_bool": Provide(second_dependency),
    },
)
```

!!! note
    The same rules for [overriding dependencies](2-overriding-dependencies.md) apply here as well.
