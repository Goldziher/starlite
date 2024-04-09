from functools import partial
from typing import Any, AsyncGenerator, Generator

import pytest

from litestar.di import Provide
from litestar.exceptions import ImproperlyConfiguredException, LitestarWarning
from litestar.types import Empty


def generator_func() -> Generator[float, None, None]:
    yield 0.1


async def async_generator_func() -> AsyncGenerator[float, None]:
    yield 0.1


async def async_callable(val: str = "three-one") -> str:
    return val


def sync_callable(val: str = "three-one") -> str:
    return val


async_partial = partial(async_callable, "why-three-and-one")
sync_partial = partial(sync_callable, "why-three-and-one")


class C:
    val = 31

    def __init__(self) -> None:
        self.val = 13

    @classmethod
    async def async_class(cls) -> int:
        return cls.val

    @classmethod
    def sync_class(cls) -> int:
        return cls.val

    @staticmethod
    async def async_static() -> str:
        return "one-three"

    @staticmethod
    def sync_static() -> str:
        return "one-three"

    async def async_instance(self) -> int:
        return self.val

    def sync_instance(self) -> int:
        return self.val


async def test_provide_default(anyio_backend: str) -> None:
    provider = Provide(dependency=async_callable)
    value = await provider()
    assert value == "three-one"


async def test_provide_cached(anyio_backend: str) -> None:
    provider = Provide(dependency=async_callable, use_cache=True)
    assert provider.value is Empty
    value = await provider()
    assert value == "three-one"
    assert provider.value == value
    second_value = await provider()
    assert value == second_value
    third_value = await provider()
    assert value == third_value


async def test_run_in_thread(anyio_backend: str) -> None:
    provider = Provide(dependency=sync_callable, sync_to_thread=True)
    value = await provider()
    assert value == "three-one"


def test_provider_equality_check() -> None:
    first_provider = Provide(dependency=sync_callable, sync_to_thread=False)
    second_provider = Provide(dependency=sync_callable, sync_to_thread=False)
    assert first_provider == second_provider
    third_provider = Provide(dependency=sync_callable, use_cache=True, sync_to_thread=False)
    assert first_provider != third_provider
    second_provider.value = True
    assert first_provider != second_provider


@pytest.mark.parametrize(
    "fn, exp",
    [
        (C.async_class, 31),
        (C.sync_class, 31),
        (C.async_static, "one-three"),
        (C.sync_static, "one-three"),
        (C().async_instance, 13),
        (C().sync_instance, 13),
        (async_callable, "three-one"),
        (sync_callable, "three-one"),
        (async_partial, "why-three-and-one"),
        (sync_partial, "why-three-and-one"),
    ],
)
@pytest.mark.usefixtures("disable_warn_sync_to_thread_with_async")
async def test_provide_for_callable(fn: Any, exp: Any, anyio_backend: str) -> None:
    assert await Provide(fn, sync_to_thread=False)() == exp


@pytest.mark.usefixtures("enable_warn_implicit_sync_to_thread")
def test_sync_callable_without_sync_to_thread_warns() -> None:
    def func() -> None:
        pass

    with pytest.warns(LitestarWarning, match="discouraged since synchronous callables"):
        Provide(func)


@pytest.mark.parametrize("sync_to_thread", [True, False])
def test_async_callable_with_sync_to_thread_warns(sync_to_thread: bool) -> None:
    async def func() -> None:
        pass

    with pytest.warns(LitestarWarning, match="asynchronous callable"):
        Provide(func, sync_to_thread=sync_to_thread)


def test_generator_with_sync_to_thread_warns() -> None:
    def func() -> Generator[int, None, None]:
        yield 1

    with pytest.warns(LitestarWarning, match="Use of generator"):
        Provide(func, sync_to_thread=True)


@pytest.mark.parametrize(
    ("dep", "exp"),
    [
        (sync_callable, True),
        (async_callable, False),
        (generator_func, True),
        (async_generator_func, True),
    ],
)
def test_dependency_has_async_callable(dep: Any, exp: bool) -> None:
    assert Provide(dep).has_sync_callable is exp


def test_raises_when_dependency_is_not_callable() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        Provide(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("dep",),
    [
        (generator_func,),
        (async_generator_func,),
    ],
)
def test_raises_when_generator_dependency_is_cached(dep: Any) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        Provide(dep, use_cache=True)
