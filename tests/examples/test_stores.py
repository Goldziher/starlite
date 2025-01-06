from pathlib import Path
from unittest.mock import MagicMock, patch

import anyio
import pytest

from litestar import get
from litestar.stores.file import FileStore
from litestar.stores.memory import MemoryStore
from litestar.stores.redis import RedisStore
from litestar.testing import TestClient

pytestmark = pytest.mark.anyio


@patch("litestar.stores.redis.Redis")
async def test_configure_integrations_set_names(mock_redis: MagicMock) -> None:
    from docs.examples.stores.configure_integrations_set_names import app

    assert isinstance(app.stores.get("redis"), RedisStore)
    assert isinstance(app.stores.get("file"), FileStore)
    assert app.stores.get("file").path == Path("data")


async def test_delete_expired_after_response(frozen_datetime) -> None:
    from docs.examples.stores.delete_expired_after_response import app, memory_store

    @get()
    async def handler() -> bytes:
        return (await memory_store.get("foo")) or b""

    app.register(handler)
    await memory_store.set("foo", "bar", expires_in=1)

    with TestClient(app) as client:
        assert client.get("/").content == b"bar"
        frozen_datetime.shift(1)
        client.get("/")
        assert client.get("/").content == b""


async def test_delete_expired_on_startup(tmp_path) -> None:
    from docs.examples.stores.delete_expired_on_startup import app, file_store

    file_store.path = anyio.Path(tmp_path)

    await file_store.set("foo", "bar", expires_in=0.01)
    await anyio.sleep(0.01)

    with TestClient(app):
        assert not await file_store.exists("foo")


async def test_get_set(capsys) -> None:
    from docs.examples.stores.get_set import main

    await main()

    assert capsys.readouterr().out == "None\nb'value'\n"


async def test_registry() -> None:
    from docs.examples.stores.registry import app, memory_store, some_other_store

    assert app.stores.get("memory") is memory_store
    assert isinstance(memory_store, MemoryStore)
    assert isinstance(some_other_store, MemoryStore)
    assert some_other_store is not memory_store


async def test_registry_access_integration() -> None:
    from docs.examples.stores.registry_access_integration import app, rate_limit_store

    assert app.stores.get("rate_limit") is rate_limit_store
    # this is a weird assertion but the easiest way to check if our example is correct
    assert app.middleware[0].kwargs["config"].get_store_from_app(app) is rate_limit_store


@patch("litestar.stores.redis.Redis")
async def test_configure_integrations(mock_redis: MagicMock) -> None:
    from docs.examples.stores.registry_configure_integrations import app

    session_store = app.middleware[0].kwargs["backend"].config.get_store_from_app(app)
    cache_store = app.response_cache_config.get_store_from_app(app)

    assert isinstance(session_store, RedisStore)
    assert isinstance(cache_store, FileStore)
    assert cache_store.path == Path("response-cache")


async def test_registry_default_factory() -> None:
    from docs.examples.stores.registry_default_factory import app, memory_store

    assert app.stores.get("foo") is memory_store
    assert app.stores.get("bar") is memory_store


@patch("litestar.stores.redis.Redis")
async def test_default_factory_namespacing(mock_redis: MagicMock) -> None:
    from docs.examples.stores.registry_default_factory_namespacing import app, root_store

    foo_store = app.stores.get("foo")
    assert isinstance(foo_store, RedisStore)
    assert foo_store._redis is root_store._redis
    assert foo_store.namespace == "LITESTAR_foo"
