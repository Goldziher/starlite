from typing import Annotated, Any

from litestar import Litestar, get
from litestar.params import Dependency


@get("/", sync_to_thread=False)
def hello_world(optional_dependency: Annotated[int, Dependency(default=3)]) -> dict[str, Any]:
    """Notice we haven't provided the dependency to the route.

    This is OK, because of the default value, and now the parameter is excluded from the docs.
    """
    return {"hello": optional_dependency}


app = Litestar(route_handlers=[hello_world])
