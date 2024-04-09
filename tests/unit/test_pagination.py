from itertools import islice
from typing import Any, List, Optional, Tuple

import pytest

from litestar import get
from litestar.app import DEFAULT_OPENAPI_CONFIG
from litestar.pagination import (
    AbstractAsyncClassicPaginator,
    AbstractAsyncCursorPaginator,
    AbstractAsyncOffsetPaginator,
    AbstractSyncClassicPaginator,
    AbstractSyncCursorPaginator,
    AbstractSyncOffsetPaginator,
    ClassicPagination,
    CursorPagination,
    OffsetPagination,
)
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client
from tests.models import DataclassPerson, DataclassPersonFactory


class TestSyncClassicPaginator(AbstractSyncClassicPaginator[DataclassPerson]):
    __test__ = False

    def __init__(self, data: List[DataclassPerson]):
        self.data = data

    def get_total(self, page_size: int) -> int:
        return round(len(self.data) / page_size)

    def get_items(self, page_size: int, current_page: int) -> List[DataclassPerson]:
        return [self.data[i : i + page_size] for i in range(0, len(self.data), page_size)][current_page - 1]


class TestAsyncClassicPaginator(AbstractAsyncClassicPaginator[DataclassPerson]):
    __test__ = False

    def __init__(self, data: List[DataclassPerson]):
        self.data = data

    async def get_total(self, page_size: int) -> int:
        return round(len(self.data) / page_size)

    async def get_items(self, page_size: int, current_page: int) -> List[DataclassPerson]:
        return [self.data[i : i + page_size] for i in range(0, len(self.data), page_size)][current_page - 1]


class TestSyncOffsetPaginator(AbstractSyncOffsetPaginator[DataclassPerson]):
    __test__ = False

    def __init__(self, data: List[DataclassPerson]):
        self.data = data

    def get_total(self) -> int:
        return len(self.data)

    def get_items(self, limit: int, offset: int) -> List[DataclassPerson]:
        return list(islice(islice(self.data, offset, None), limit))


class TestAsyncOffsetPaginator(AbstractAsyncOffsetPaginator[DataclassPerson]):
    __test__ = False

    def __init__(self, data: List[DataclassPerson]):
        self.data = data

    async def get_total(self) -> int:
        return len(self.data)

    async def get_items(self, limit: int, offset: int) -> List[DataclassPerson]:
        return list(islice(islice(self.data, offset, None), limit))


data = DataclassPersonFactory.batch(50)


@pytest.mark.parametrize("paginator", (TestSyncClassicPaginator(data=data), TestAsyncClassicPaginator(data=data)))
def test_classic_pagination_data_shape(paginator: Any) -> None:
    @get("/async")
    async def async_handler(page_size: int, current_page: int) -> ClassicPagination[DataclassPerson]:
        return await paginator(page_size=page_size, current_page=current_page)  # type: ignore[no-any-return]

    @get("/sync")
    def sync_handler(page_size: int, current_page: int) -> ClassicPagination[DataclassPerson]:
        return paginator(page_size=page_size, current_page=current_page)  # type: ignore[no-any-return]

    with create_test_client([async_handler, sync_handler]) as client:
        if isinstance(paginator, TestSyncClassicPaginator):
            response = client.get("/sync", params={"page_size": 5, "current_page": 1})
        else:
            response = client.get("/async", params={"page_size": 5, "current_page": 1})
        assert response.status_code == HTTP_200_OK

        response_data = response.json()
        assert len(response_data["items"]) == 5
        assert response_data["total_pages"] == 10
        assert response_data["page_size"] == 5
        assert response_data["current_page"] == 1


@pytest.mark.parametrize("paginator", (TestSyncClassicPaginator(data=data), TestAsyncClassicPaginator(data=data)))
def test_classic_pagination_openapi_schema(paginator: Any) -> None:
    @get("/async")
    async def async_handler(page_size: int, current_page: int) -> ClassicPagination[DataclassPerson]:
        return await paginator(page_size=page_size, current_page=current_page)  # type: ignore[no-any-return]

    @get("/sync")
    def sync_handler(page_size: int, current_page: int) -> ClassicPagination[DataclassPerson]:
        return paginator(page_size=page_size, current_page=current_page)  # type: ignore[no-any-return]

    with create_test_client([async_handler, sync_handler], openapi_config=DEFAULT_OPENAPI_CONFIG) as client:
        schema = client.app.openapi_schema
        assert schema

        path = "/sync" if isinstance(paginator, TestSyncClassicPaginator) else "/async"

        spec = schema.to_schema()["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]
        assert spec == {
            "schema": {
                "properties": {
                    "items": {
                        "items": {"$ref": "#/components/schemas/DataclassPerson"},
                        "type": "array",
                    },
                    "page_size": {"type": "integer", "description": "Number of items per page."},
                    "current_page": {"type": "integer", "description": "Current page number."},
                    "total_pages": {"type": "integer", "description": "Total number of pages."},
                },
                "type": "object",
            }
        }


@pytest.mark.parametrize("paginator", (TestSyncOffsetPaginator(data=data), TestAsyncOffsetPaginator(data=data)))
def test_limit_offset_pagination_data_shape(paginator: Any) -> None:
    @get("/async")
    async def async_handler(limit: int, offset: int) -> OffsetPagination[DataclassPerson]:
        return await paginator(limit=limit, offset=offset)  # type: ignore[no-any-return]

    @get("/sync")
    def sync_handler(limit: int, offset: int) -> OffsetPagination[DataclassPerson]:
        return paginator(limit=limit, offset=offset)  # type: ignore[no-any-return]

    with create_test_client([async_handler, sync_handler]) as client:
        if isinstance(paginator, TestSyncOffsetPaginator):
            response = client.get("/sync", params={"limit": 5, "offset": 0})
        else:
            response = client.get("/async", params={"limit": 5, "offset": 0})
        assert response.status_code == HTTP_200_OK

        response_data = response.json()
        assert len(response_data["items"]) == 5
        assert response_data["total"] == 50
        assert response_data["limit"] == 5
        assert response_data["offset"] == 0


@pytest.mark.parametrize("paginator", (TestSyncOffsetPaginator(data=data), TestAsyncOffsetPaginator(data=data)))
def test_limit_offset_pagination_openapi_schema(paginator: Any) -> None:
    @get("/async")
    async def async_handler(limit: int, offset: int) -> OffsetPagination[DataclassPerson]:
        return await paginator(limit=limit, offset=offset)  # type: ignore[no-any-return]

    @get("/sync")
    def sync_handler(limit: int, offset: int) -> OffsetPagination[DataclassPerson]:
        return paginator(limit=limit, offset=offset)  # type: ignore[no-any-return]

    with create_test_client([async_handler, sync_handler], openapi_config=DEFAULT_OPENAPI_CONFIG) as client:
        schema = client.app.openapi_schema
        assert schema

        path = "/sync" if isinstance(paginator, TestSyncOffsetPaginator) else "/async"

        spec = schema.to_schema()["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]
        assert spec == {
            "schema": {
                "properties": {
                    "items": {
                        "items": {"$ref": "#/components/schemas/DataclassPerson"},
                        "type": "array",
                    },
                    "limit": {"type": "integer", "description": "Maximal number of items to send."},
                    "offset": {"type": "integer", "description": "Offset from the beginning of the query."},
                    "total": {"type": "integer", "description": "Total number of items."},
                },
                "type": "object",
            }
        }


class TestSyncCursorPagination(AbstractSyncCursorPaginator[str, DataclassPerson]):
    __test__ = False

    def __init__(self, data: List[DataclassPerson]):
        self.data = data

    def get_items(self, cursor: Optional[str], results_per_page: int) -> "Tuple[List[DataclassPerson], Optional[str]]":
        results = self.data[:results_per_page]
        return results, results[-1].id


class TestAsyncCursorPagination(AbstractAsyncCursorPaginator[str, DataclassPerson]):
    __test__ = False

    def __init__(self, data: List[DataclassPerson]):
        self.data = data

    async def get_items(
        self, cursor: Optional[str], results_per_page: int
    ) -> "Tuple[List[DataclassPerson], Optional[str]]":
        results = self.data[:results_per_page]
        return results, results[-1].id


@pytest.mark.parametrize("paginator", (TestSyncCursorPagination(data=data), TestAsyncCursorPagination(data=data)))
def test_cursor_pagination_data_shape(paginator: Any) -> None:
    @get("/async")
    async def async_handler(cursor: Optional[str] = None) -> CursorPagination[str, DataclassPerson]:
        return await paginator(cursor=cursor, results_per_page=5)  # type: ignore[no-any-return]

    @get("/sync")
    def sync_handler(cursor: Optional[str] = None) -> CursorPagination[str, DataclassPerson]:
        return paginator(cursor=cursor, results_per_page=5)  # type: ignore[no-any-return]

    with create_test_client([async_handler, sync_handler]) as client:
        if isinstance(paginator, TestSyncCursorPagination):
            response = client.get("/sync")
        else:
            response = client.get("/async")
        assert response.status_code == HTTP_200_OK

        response_data = response.json()
        assert len(response_data["items"]) == 5
        assert response_data["results_per_page"] == 5
        assert response_data["cursor"] == data[4].id


@pytest.mark.parametrize("paginator", (TestSyncCursorPagination(data=data), TestAsyncCursorPagination(data=data)))
def test_cursor_pagination_openapi_schema(paginator: Any) -> None:
    @get("/async")
    async def async_handler(cursor: Optional[str] = None) -> CursorPagination[str, DataclassPerson]:
        return await paginator(cursor=cursor, results_per_page=5)  # type: ignore[no-any-return]

    @get("/sync")
    def sync_handler(cursor: Optional[str] = None) -> CursorPagination[str, DataclassPerson]:
        return paginator(cursor=cursor, results_per_page=5)  # type: ignore[no-any-return]

    with create_test_client([async_handler, sync_handler], openapi_config=DEFAULT_OPENAPI_CONFIG) as client:
        schema = client.app.openapi_schema
        assert schema

        path = "/sync" if isinstance(paginator, TestSyncCursorPagination) else "/async"

        spec = schema.to_schema()["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]
        assert spec == {
            "schema": {
                "properties": {
                    "items": {
                        "items": {"$ref": "#/components/schemas/DataclassPerson"},
                        "type": "array",
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Unique ID, designating the last identifier in the given data set. This value can be used to request the 'next' batch of records.",
                    },
                    "results_per_page": {"type": "integer", "description": "Maximal number of items to send."},
                },
                "type": "object",
            }
        }
