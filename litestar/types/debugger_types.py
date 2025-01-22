from types import TracebackType
from typing import Protocol,  Type, Optional, Union, NoReturn, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


class PDBProtocol(Protocol):
    @staticmethod
    def post_mortem(
        t: Optional[TracebackType] = None,
    ) -> Optional[NoReturn]: ...


class IPDBProtocol(Protocol):
    @staticmethod
    def post_mortem(
        tb: Optional[TracebackType] = None,
    ) -> Optional[NoReturn]: ...


class PDBRProtocol(Protocol):
    @staticmethod
    def post_mortem(
        traceback: Optional[TracebackType] = None,
        value: Optional[BaseException] = None,
    ) -> Optional[NoReturn]: ...


class PUDBProtocol(Protocol):
    @staticmethod
    def post_mortem(
        tb: Optional[TracebackType] = None,
        e_type: Optional[Type[BaseException]] = None,
        e_value: Optional[BaseException] = None,
    ) -> Optional[NoReturn]: ...


Debugger: TypeAlias = Union[PDBProtocol, IPDBProtocol, PDBRProtocol, PUDBProtocol]
