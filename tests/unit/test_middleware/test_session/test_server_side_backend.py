from secrets import token_hex
from typing import TYPE_CHECKING

import pytest

from litestar import Litestar, Request, get
from litestar.exceptions import ImproperlyConfiguredException
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.serialization import encode_json
from litestar.stores.memory import MemoryStore
from litestar.testing import TestClient

if TYPE_CHECKING:
    from time_machine import Coordinates

    from litestar.middleware.session.server_side import ServerSideSessionBackend

pytestmark = pytest.mark.anyio


def generate_session_data() -> bytes:
    return encode_json({token_hex(): token_hex()})


@pytest.fixture
def session_data() -> bytes:
    return generate_session_data()


async def test_non_default_store(memory_store: MemoryStore) -> None:
    @get("/")
    def handler(request: Request) -> None:
        request.set_session({"foo": "bar"})
        return

    app = Litestar([handler], middleware=[ServerSideSessionConfig().middleware], stores={"sessions": memory_store})

    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert await memory_store.exists(res.cookies["session"])


async def test_set_store_name(memory_store: MemoryStore) -> None:
    @get("/")
    def handler(request: Request) -> None:
        request.set_session({"foo": "bar"})
        return

    app = Litestar(
        [handler],
        middleware=[ServerSideSessionConfig(store="some_store").middleware],
        stores={"some_store": memory_store},
    )

    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert await memory_store.exists(res.cookies["session"])


async def test_get_set(
    server_side_session_backend: "ServerSideSessionBackend", session_data: bytes, memory_store: MemoryStore
) -> None:
    await server_side_session_backend.set("foo", session_data, memory_store)
    loaded = await server_side_session_backend.get("foo", memory_store)

    assert loaded == session_data


async def test_get_renew_on_access(
    server_side_session_backend: "ServerSideSessionBackend",
    session_data: bytes,
    memory_store: MemoryStore,
    frozen_datetime: "Coordinates",
) -> None:
    server_side_session_backend.config.max_age = 1
    server_side_session_backend.config.renew_on_access = True

    await server_side_session_backend.set("foo", session_data, memory_store)
    server_side_session_backend.config.max_age = 10

    await server_side_session_backend.get("foo", memory_store)

    frozen_datetime.shift(1.01)

    assert await server_side_session_backend.get("foo", memory_store) is not None


async def test_get_set_multiple_returns_correct_identity(
    server_side_session_backend: "ServerSideSessionBackend", memory_store: MemoryStore
) -> None:
    foo_data = generate_session_data()
    bar_data = generate_session_data()
    await server_side_session_backend.set("foo", foo_data, memory_store)
    await server_side_session_backend.set("bar", bar_data, memory_store)

    loaded = await server_side_session_backend.get("foo", memory_store)

    assert loaded == foo_data


async def test_delete(server_side_session_backend: "ServerSideSessionBackend", memory_store: MemoryStore) -> None:
    await server_side_session_backend.set("foo", generate_session_data(), memory_store)
    await server_side_session_backend.set("bar", generate_session_data(), memory_store)

    await server_side_session_backend.delete("foo", memory_store)

    assert not await server_side_session_backend.get("foo", memory_store)
    assert await server_side_session_backend.get("bar", memory_store)


async def test_delete_idempotence(
    server_side_session_backend: "ServerSideSessionBackend", session_data: bytes, memory_store: MemoryStore
) -> None:
    await server_side_session_backend.set("foo", session_data, memory_store)

    await server_side_session_backend.delete("foo", memory_store)
    await server_side_session_backend.delete("foo", memory_store)  # ensure this doesn't raise an error


async def test_max_age_expires(
    server_side_session_backend: "ServerSideSessionBackend",
    session_data: bytes,
    memory_store: MemoryStore,
    frozen_datetime: "Coordinates",
) -> None:
    server_side_session_backend.config.max_age = 1
    await server_side_session_backend.set("foo", session_data, memory_store)

    frozen_datetime.shift(1)

    assert not await server_side_session_backend.get("foo", memory_store)


@pytest.mark.parametrize(
    "key, should_raise",
    [
        ["", True],
        ["a", False],
        ["a" * 256, False],
        ["a" * 257, True],
    ],
)
def test_key_validation(server_side_session_backend: "ServerSideSessionBackend", key: str, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            ServerSideSessionConfig(key=key)
    else:
        ServerSideSessionConfig(key=key)


@pytest.mark.parametrize(
    "max_age, should_raise",
    [
        [0, True],
        [-1, True],
        [1, False],
        [100, False],
    ],
)
def test_max_age_validation(
    server_side_session_backend: "ServerSideSessionBackend", max_age: int, should_raise: bool
) -> None:
    if should_raise:
        with pytest.raises(ImproperlyConfiguredException):
            ServerSideSessionConfig(key="a", max_age=max_age)
    else:
        ServerSideSessionConfig(key="a", max_age=max_age)
