from types import ModuleType, TracebackType
from typing import Any, Optional, Protocol, Union

from typing_extensions import TypeAlias


class PDBProtocol(Protocol):
    @staticmethod
    def post_mortem(
        traceback: Optional[TracebackType] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...


Debugger: TypeAlias = Union[ModuleType, PDBProtocol]
