from inspect import Parameter, Signature
from typing import Any, Dict, Tuple

from litestar import Litestar, get
from litestar.di import Provide
from litestar.plugins import DIPlugin


class MyBaseType:
    def __init__(self, param):
        self.param = param


class MyDIPlugin(DIPlugin):
    def has_typed_init(self, type_: Any) -> bool:
        return issubclass(type_, MyBaseType)

    def get_typed_init(self, type_: Any) -> Tuple[Signature, Dict[str, Any]]:
        signature = Signature([Parameter(name="param", kind=Parameter.POSITIONAL_OR_KEYWORD)])
        annotations = {"param": str}
        return signature, annotations


@get("/", dependencies={"injected": Provide(MyBaseType, sync_to_thread=False)})
async def handler(injected: MyBaseType) -> str:
    return injected.param


app = Litestar(route_handlers=[handler], plugins=[MyDIPlugin()])

# run: /?param=hello
