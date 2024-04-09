from collections import defaultdict, deque
from dataclasses import MISSING, dataclass
from functools import partial
from inspect import Signature
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    ClassVar,
    DefaultDict,
    Deque,
    Dict,
    FrozenSet,
    Generic,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import pytest
from typing_extensions import Annotated

from litestar import Response, get
from litestar.pagination import CursorPagination
from litestar.types import Empty
from litestar.utils import is_any, is_async_callable, is_class_and_subclass, is_optional_union, is_union
from litestar.utils.predicates import (
    is_class_var,
    is_dataclass_class,
    is_generic,
    is_mapping,
    is_non_string_iterable,
    is_non_string_sequence,
    is_undefined_sentinel,
)


class C:
    pass


@get("/", sync_to_thread=False)
def naive_handler() -> Dict[str, int]:
    return {}


@get("/", sync_to_thread=False)
def response_handler() -> Response[Any]:
    return Response(content=b"")


class Sub(C): ...


@pytest.mark.parametrize(
    "args, expected",
    (
        ((Sub, C), True),
        ((Signature.from_callable(cast("Any", naive_handler.fn)).return_annotation, C), False),
        ((Signature.from_callable(cast("Any", response_handler.fn)).return_annotation, Response), True),
        ((Dict[str, Any], C), False),
        ((C(), C), False),
    ),
)
def test_is_class_and_subclass(args: Tuple[Any, Any], expected: bool) -> None:
    assert is_class_and_subclass(*args) is expected


@pytest.mark.parametrize(
    "value, expected",
    (
        (
            (Tuple[int, ...], True),
            (Tuple[int], True),
            (List[str], True),
            (Set[str], True),
            (FrozenSet[str], True),
            (Deque[str], True),
            (Sequence[str], True),
            (Iterable[str], True),
            (list, True),
            (tuple, True),
            (deque, True),
            (set, True),
            (frozenset, True),
            (str, False),
            (bytes, False),
            (dict, True),
            (Dict[str, Any], True),
            (Union[str, int], False),
            (1, False),
        )
    ),
)
def test_is_non_string_iterable(value: Any, expected: bool) -> None:
    assert is_non_string_iterable(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    (
        (
            (Tuple[int, ...], True),
            (Tuple[int], True),
            (List[str], True),
            (Set[str], True),
            (FrozenSet[str], True),
            (Deque[str], True),
            (Sequence[str], True),
            (Iterable[str], False),
            (list, True),
            (tuple, True),
            (deque, True),
            (set, True),
            (frozenset, True),
            (str, False),
            (bytes, False),
            (dict, False),
            (Dict[str, Any], False),
            (Union[str, int], False),
            (1, False),
        )
    ),
)
def test_is_non_string_sequence(value: Any, expected: bool) -> None:
    assert is_non_string_sequence(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    ((CursorPagination[str, str], True), (dict, False)),
)
def test_is_generic(value: Any, expected: bool) -> None:
    assert is_generic(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    (
        (Dict, True),
        (dict, True),
        (defaultdict, True),
        (DefaultDict, True),
        (Mapping, True),
        (MutableMapping, True),
        (list, False),
        (Iterable, False),
    ),
)
def test_is_mapping(value: Any, expected: bool) -> None:
    assert is_mapping(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    ((Any, True), (Union[Any, str], True), (int, False), (dict, False), (Dict[str, Any], False), (None, False)),
)
def test_is_any(value: Any, expected: bool) -> None:
    assert is_any(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    (
        (Optional[int], True),
        (Optional[Union[int, str]], True),
        (Union[str, None], True),
        (None, False),
        (int, False),
        (Union[int, str], True),
    ),
)
def test_is_union(value: Any, expected: bool) -> None:
    assert is_union(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    (
        (Optional[int], True),
        (Optional[Union[int, str]], True),
        (Union[str, None], True),
        (None, False),
        (int, False),
        (Union[int, str], False),
    ),
)
def test_is_optional_union(value: Any, expected: bool) -> None:
    assert is_optional_union(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    (
        (ClassVar[int], True),
        (Annotated[ClassVar[int], "abc"], True),
        (Dict[str, int], False),
        (None, False),
    ),
)
def test_is_class_var(value: Any, expected: bool) -> None:
    assert is_class_var(value) is expected


class AsyncTestCallable:
    async def __call__(self, param1: int, param2: int) -> None: ...

    async def method(self, param1: int, param2: int) -> None: ...


async def async_generator() -> AsyncGenerator[int, None]:
    yield 1


class SyncTestCallable:
    def __call__(self, param1: int, param2: int) -> None: ...

    def method(self, param1: int, param2: int) -> None: ...


async def async_func(param1: int, param2: int) -> None: ...


def sync_func(param1: int, param2: int) -> None: ...


async_callable = AsyncTestCallable()
sync_callable = SyncTestCallable()


@pytest.mark.parametrize(
    "c, exp",
    [
        (async_callable, True),
        (sync_callable, False),
        (async_callable.method, True),
        (sync_callable.method, False),
        (async_func, True),
        (sync_func, False),
        (lambda: ..., False),
        (AsyncTestCallable, True),
        (SyncTestCallable, False),
        (async_generator, False),
    ],
)
def test_is_async_callable(c: Callable[[int, int], None], exp: bool) -> None:
    assert is_async_callable(c) is exp
    partial_1 = partial(c, 1)
    assert is_async_callable(partial_1) is exp
    partial_2 = partial(partial_1, 2)
    assert is_async_callable(partial_2) is exp


def test_not_undefined_sentinel() -> None:
    assert is_undefined_sentinel(Signature.empty) is True
    assert is_undefined_sentinel(Empty) is True
    assert is_undefined_sentinel(Ellipsis) is True
    assert is_undefined_sentinel(MISSING) is True
    assert is_undefined_sentinel(1) is False
    assert is_undefined_sentinel("") is False
    assert is_undefined_sentinel([]) is False
    assert is_undefined_sentinel({}) is False
    assert is_undefined_sentinel(None) is False


T = TypeVar("T")


@dataclass
class NonGenericDataclass:
    foo: int


@dataclass
class GenericDataclass(Generic[T]):
    foo: T


class NonDataclass: ...


@pytest.mark.parametrize(
    ("cls", "expected"),
    ((NonGenericDataclass, True), (GenericDataclass, True), (GenericDataclass[int], True), (NonDataclass, False)),
)
def test_is_dataclass_class(cls: Any, expected: bool) -> None:
    assert is_dataclass_class(cls) is expected
