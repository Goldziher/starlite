import gzip
import random
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, Type, Union
from unittest.mock import MagicMock
from uuid import uuid4

import msgspec
import pytest

from litestar import Litestar, Request, Response, get, post
from litestar.config.compression import CompressionConfig
from litestar.config.response_cache import CACHE_FOREVER, ResponseCacheConfig
from litestar.enums import CompressionEncoding
from litestar.middleware.response_cache import ResponseCacheMiddleware
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.stores.base import Store
from litestar.stores.memory import MemoryStore
from litestar.testing import TestClient, create_test_client
from litestar.types import HTTPScope

if TYPE_CHECKING:
    from time_machine import Coordinates


@pytest.fixture()
def mock() -> MagicMock:
    return MagicMock(return_value=str(random.random()))


def after_request_handler(response: "Response") -> "Response":
    response.headers["unique-identifier"] = str(uuid4())
    return response


@pytest.mark.parametrize("sync_to_thread", (True, False))
def test_default_cache_response(sync_to_thread: bool, mock: MagicMock) -> None:
    @get(
        "/cached",
        sync_to_thread=sync_to_thread,
        cache=True,
        type_encoders={int: str},  # test pickling issues. see https://github.com/litestar-org/litestar/issues/1096
    )
    def handler() -> str:
        return mock()  # type: ignore[no-any-return]

    with create_test_client([handler], after_request=after_request_handler) as client:
        first_response = client.get("/cached")
        second_response = client.get("/cached")

        first_response_identifier = first_response.headers["unique-identifier"]

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert second_response.headers["unique-identifier"] == first_response_identifier
        assert first_response.text == second_response.text
        assert mock.call_count == 1


def test_handler_expiration(mock: MagicMock, frozen_datetime: "Coordinates") -> None:
    @get("/cached-local", cache=10)
    async def handler() -> str:
        return mock()  # type: ignore[no-any-return]

    with create_test_client([handler], after_request=after_request_handler) as client:
        first_response = client.get("/cached-local")
        frozen_datetime.shift(delta=timedelta(seconds=5))
        second_response = client.get("/cached-local")
        assert first_response.headers["unique-identifier"] == second_response.headers["unique-identifier"]
        assert mock.call_count == 1

        frozen_datetime.shift(delta=timedelta(seconds=11))
        third_response = client.get("/cached-local")
        assert first_response.headers["unique-identifier"] != third_response.headers["unique-identifier"]
        assert mock.call_count == 2


def test_default_expiration(mock: MagicMock, frozen_datetime: "Coordinates") -> None:
    @get("/cached-default", cache=True)
    async def handler() -> str:
        return mock()  # type: ignore[no-any-return]

    with create_test_client(
        [handler], after_request=after_request_handler, response_cache_config=ResponseCacheConfig(default_expiration=1)
    ) as client:
        first_response = client.get("/cached-default")
        second_response = client.get("/cached-default")
        assert first_response.headers["unique-identifier"] == second_response.headers["unique-identifier"]
        assert mock.call_count == 1

        frozen_datetime.shift(delta=timedelta(seconds=1))
        third_response = client.get("/cached-default")
        assert first_response.headers["unique-identifier"] != third_response.headers["unique-identifier"]
        assert mock.call_count == 2


@pytest.mark.parametrize("expiration,expected_expiration", [(True, None), (10, 10)])
def test_default_expiration_none(
    memory_store: MemoryStore, expiration: int, expected_expiration: Optional[int]
) -> None:
    @get("/cached", cache=expiration)
    def handler() -> None:
        return None

    app = Litestar(
        [handler],
        stores={"response_cache": memory_store},
        response_cache_config=ResponseCacheConfig(default_expiration=None),
    )

    with TestClient(app) as client:
        client.get("/cached")

    if expected_expiration is None:
        assert memory_store._store["GET/cached"].expires_at is None
    else:
        assert memory_store._store["GET/cached"].expires_at


def test_cache_forever(memory_store: MemoryStore) -> None:
    @get("/cached", cache=CACHE_FOREVER)
    async def handler() -> None:
        return None

    app = Litestar([handler], stores={"response_cache": memory_store})

    with TestClient(app) as client:
        client.get("/cached")

    assert memory_store._store["GET/cached"].expires_at is None


@pytest.mark.parametrize("sync_to_thread", (True, False))
async def test_custom_cache_key(sync_to_thread: bool, anyio_backend: str, mock: MagicMock) -> None:
    def custom_cache_key_builder(request: Request) -> str:
        return f"{request.url.path}:::cached"

    @get("/cached", sync_to_thread=sync_to_thread, cache=True, cache_key_builder=custom_cache_key_builder)
    def handler() -> str:
        return mock()  # type: ignore[no-any-return]

    app = Litestar([handler])

    with TestClient(app) as client:
        client.get("/cached")
        store = app.stores.get("response_cache")
        assert await store.exists("/cached:::cached")


async def test_non_default_store_name(mock: MagicMock) -> None:
    @get(cache=True)
    def handler() -> str:
        return mock()  # type: ignore[no-any-return]

    app = Litestar([handler], response_cache_config=ResponseCacheConfig(store="some_store"))

    with TestClient(app=app) as client:
        response_one = client.get("/")
        assert response_one.status_code == 200
        assert response_one.text == mock.return_value

        response_two = client.get("/")
        assert response_two.status_code == 200
        assert response_two.text == mock.return_value

        assert mock.call_count == 1

    assert await app.stores.get("some_store").exists("GET/")


async def test_with_stores(store: Store, mock: MagicMock) -> None:
    @get(cache=True)
    def handler() -> str:
        return mock()  # type: ignore[no-any-return]

    app = Litestar([handler], stores={"response_cache": store})

    with TestClient(app=app) as client:
        response_one = client.get("/")
        assert response_one.status_code == 200
        assert response_one.text == mock.return_value

        response_two = client.get("/")
        assert response_two.status_code == 200
        assert response_two.text == mock.return_value

        assert mock.call_count == 1


def test_does_not_apply_to_non_cached_routes(mock: MagicMock) -> None:
    @get("/")
    def handler() -> str:
        return mock()  # type: ignore[no-any-return]

    with create_test_client([handler]) as client:
        first_response = client.get("/")
        second_response = client.get("/")

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert mock.call_count == 2


@pytest.mark.parametrize(
    "cache,expect_applied",
    [
        (True, True),
        (False, False),
        (1, True),
        (CACHE_FOREVER, True),
    ],
)
def test_middleware_not_applied_to_non_cached_routes(
    cache: Union[bool, int, Type[CACHE_FOREVER]], expect_applied: bool
) -> None:
    @get(path="/", cache=cache)
    def handler() -> None: ...

    client = create_test_client(route_handlers=[handler])
    unpacked_middleware = []
    cur = client.app.asgi_router.root_route_map_node.children["/"].asgi_handlers["GET"][0]
    while hasattr(cur, "app"):
        unpacked_middleware.append(cur)
        cur = cur.app
    unpacked_middleware.append(cur)

    assert len([m for m in unpacked_middleware if isinstance(m, ResponseCacheMiddleware)]) == int(expect_applied)


async def test_compression_applies_before_cache() -> None:
    return_value = "_litestar_" * 4000
    mock = MagicMock(return_value=return_value)

    @get(path="/", cache=True)
    def handler_fn() -> str:
        return mock()  # type: ignore[no-any-return]

    app = Litestar(
        route_handlers=[handler_fn],
        compression_config=CompressionConfig(backend="gzip"),
    )

    with TestClient(app) as client:
        client.get("/", headers={"Accept-Encoding": str(CompressionEncoding.GZIP.value)})

    stored_value = await app.response_cache_config.get_store_from_app(app).get("GET/")
    assert stored_value
    stored_messages = msgspec.msgpack.decode(stored_value)
    assert gzip.decompress(stored_messages[1]["body"]).decode() == return_value


@pytest.mark.parametrize(
    ("response", "should_cache"),
    [
        (HTTP_200_OK, True),
        (HTTP_400_BAD_REQUEST, False),
        (HTTP_500_INTERNAL_SERVER_ERROR, False),
        (RuntimeError, False),
    ],
)
def test_default_do_response_cache_predicate(
    mock: MagicMock, response: Union[int, Type[RuntimeError]], should_cache: bool
) -> None:
    @get("/", cache=True)
    def handler() -> Response:
        mock()
        if isinstance(response, int):
            return Response(None, status_code=response)
        raise RuntimeError

    with create_test_client([handler]) as client:
        client.get("/")
        client.get("/")
        assert mock.call_count == 1 if should_cache else 2


def test_custom_do_response_cache_predicate(mock: MagicMock) -> None:
    @get("/", cache=True)
    def handler() -> str:
        mock()
        return "OK"

    def filter_cache_response(_: HTTPScope, __: int) -> bool:
        return False

    with create_test_client(
        [handler], response_cache_config=ResponseCacheConfig(cache_response_filter=filter_cache_response)
    ) as client:
        client.get("/")
        client.get("/")
        assert mock.call_count == 2


def test_on_multiple_handlers(mock: MagicMock) -> None:
    @get("/cached-local", cache=10)
    async def handler() -> str:
        mock()
        return "get_response"

    @post("/cached-local", cache=10)
    async def handler_post() -> str:
        mock()
        return "post_response"

    with create_test_client([handler, handler_post], after_request=after_request_handler) as client:
        # POST request to have this cached
        first_post_response = client.post("/cached-local")
        assert first_post_response.status_code == HTTP_201_CREATED
        assert first_post_response.text == "post_response"
        assert mock.call_count == 1

        # GET request to verify it doesn't use the cache created by the previous POST request
        get_response = client.get("/cached-local")
        assert get_response.status_code == HTTP_200_OK
        assert get_response.text == "get_response"
        assert first_post_response.headers["unique-identifier"] != get_response.headers["unique-identifier"]
        assert mock.call_count == 2

        # POST request to verify it uses the cache generated during the initial POST request
        second_post_response = client.post("/cached-local")
        assert second_post_response.status_code == HTTP_201_CREATED
        assert second_post_response.text == "post_response"
        assert first_post_response.headers["unique-identifier"] == second_post_response.headers["unique-identifier"]
        assert mock.call_count == 2
