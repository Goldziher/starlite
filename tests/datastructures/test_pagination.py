from itertools import islice
from typing import Any, List, Optional, Tuple

import pytest

from starlite import (
    AbstractAsyncClassicPaginator,
    AbstractAsyncCursorPaginator,
    AbstractAsyncOffsetPaginator,
    AbstractSyncClassicPaginator,
    AbstractSyncCursorPaginator,
    AbstractSyncOffsetPaginator,
    ClassicPagination,
    CursorPagination,
    OffsetPagination,
    create_test_client,
    get,
)
from starlite.app import DEFAULT_OPENAPI_CONFIG
from starlite.status_codes import HTTP_200_OK
from tests import Person, PersonFactory


class TestSyncClassicPaginator(AbstractSyncClassicPaginator[Person]):
    def __init__(self, data: List[Person]):
        self.data = data

    def get_total(self, page_size: int) -> int:
        return round(len(self.data) / page_size)

    def get_items(self, page_size: int, current_page: int) -> List[Person]:
        return [self.data[i : i + page_size] for i in range(0, len(self.data), page_size)][current_page - 1]


class TestAsyncClassicPaginator(AbstractAsyncClassicPaginator[Person]):
    def __init__(self, data: List[Person]):
        self.data = data

    async def get_total(self, page_size: int) -> int:
        return round(len(self.data) / page_size)

    async def get_items(self, page_size: int, current_page: int) -> List[Person]:
        return [self.data[i : i + page_size] for i in range(0, len(self.data), page_size)][current_page - 1]


class TestSyncOffsetPaginator(AbstractSyncOffsetPaginator[Person]):
    def __init__(self, data: List[Person]):

        self.data = data

    def get_total(self) -> int:
        return len(self.data)

    def get_items(self, limit: int, offset: int) -> List[Person]:
        return list(islice(islice(self.data, offset, None), limit))


class TestAsyncOffsetPaginator(AbstractAsyncOffsetPaginator[Person]):
    def __init__(self, data: List[Person]):

        self.data = data

    async def get_total(self) -> int:
        return len(self.data)

    async def get_items(self, limit: int, offset: int) -> List[Person]:
        return list(islice(islice(self.data, offset, None), limit))


data = PersonFactory.batch(50)


@pytest.mark.parametrize("paginator", (TestSyncClassicPaginator(data=data), TestAsyncClassicPaginator(data=data)))
def test_classic_pagination_data_shape(paginator: Any) -> None:
    @get("/async")
    async def async_handler(page_size: int, current_page: int) -> ClassicPagination[Person]:
        return await paginator(page_size=page_size, current_page=current_page)  # type: ignore

    @get("/sync")
    def sync_handler(page_size: int, current_page: int) -> ClassicPagination[Person]:
        return paginator(page_size=page_size, current_page=current_page)  # type: ignore

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
    async def async_handler(page_size: int, current_page: int) -> ClassicPagination[Person]:
        return await paginator(page_size=page_size, current_page=current_page)  # type: ignore

    @get("/sync")
    def sync_handler(page_size: int, current_page: int) -> ClassicPagination[Person]:
        return paginator(page_size=page_size, current_page=current_page)  # type: ignore

    with create_test_client([async_handler, sync_handler], openapi_config=DEFAULT_OPENAPI_CONFIG) as client:
        schema = client.app.openapi_schema
        assert schema

        path = "/sync" if isinstance(paginator, TestSyncClassicPaginator) else "/async"

        spec = schema.dict(exclude_none=True)["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]
        assert spec == {
            "media_type_schema": {
                "properties": {
                    "items": {"items": {"ref": "#/components/schemas/Person"}, "type": "array"},
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
    async def async_handler(limit: int, offset: int) -> OffsetPagination[Person]:
        return await paginator(limit=limit, offset=offset)  # type: ignore

    @get("/sync")
    def sync_handler(limit: int, offset: int) -> OffsetPagination[Person]:
        return paginator(limit=limit, offset=offset)  # type: ignore

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
    async def async_handler(limit: int, offset: int) -> OffsetPagination[Person]:
        return await paginator(limit=limit, offset=offset)  # type: ignore

    @get("/sync")
    def sync_handler(limit: int, offset: int) -> OffsetPagination[Person]:
        return paginator(limit=limit, offset=offset)  # type: ignore

    with create_test_client([async_handler, sync_handler], openapi_config=DEFAULT_OPENAPI_CONFIG) as client:
        schema = client.app.openapi_schema
        assert schema

        path = "/sync" if isinstance(paginator, TestSyncOffsetPaginator) else "/async"

        spec = schema.dict(exclude_none=True)["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]
        assert spec == {
            "media_type_schema": {
                "properties": {
                    "items": {"items": {"ref": "#/components/schemas/Person"}, "type": "array"},
                    "limit": {"type": "integer", "description": "Maximal number of items to send."},
                    "offset": {"type": "integer", "description": "Offset from the beginning of the query."},
                    "total": {"type": "integer", "description": "Total number of items."},
                },
                "type": "object",
            }
        }


class TestSyncCursorPagination(AbstractSyncCursorPaginator[str, Person]):
    def __init__(self, data: List[Person]):
        self.data = data

    def get_items(self, cursor: Optional[str], results_per_page: int) -> "Tuple[List[Person], Optional[str]]":
        results = self.data[:results_per_page]
        return results, results[-1].id


class TestAsyncCursorPagination(AbstractAsyncCursorPaginator[str, Person]):
    def __init__(self, data: List[Person]):
        self.data = data

    async def get_items(self, cursor: Optional[str], results_per_page: int) -> "Tuple[List[Person], Optional[str]]":
        results = self.data[:results_per_page]
        return results, results[-1].id


@pytest.mark.parametrize("paginator", (TestSyncCursorPagination(data=data), TestAsyncCursorPagination(data=data)))
def test_cursor_pagination_data_shape(paginator: Any) -> None:
    @get("/async")
    async def async_handler(cursor: Optional[str] = None) -> CursorPagination[str, Person]:
        return await paginator(cursor=cursor, results_per_page=5)  # type: ignore

    @get("/sync")
    def sync_handler(cursor: Optional[str] = None) -> CursorPagination[str, Person]:
        return paginator(cursor=cursor, results_per_page=5)  # type: ignore

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
    async def async_handler(cursor: Optional[str] = None) -> CursorPagination[str, Person]:
        return await paginator(cursor=cursor, results_per_page=5)  # type: ignore

    @get("/sync")
    def sync_handler(cursor: Optional[str] = None) -> CursorPagination[str, Person]:
        return paginator(cursor=cursor, results_per_page=5)  # type: ignore

    with create_test_client([async_handler, sync_handler], openapi_config=DEFAULT_OPENAPI_CONFIG) as client:
        schema = client.app.openapi_schema
        assert schema

        path = "/sync" if isinstance(paginator, TestSyncCursorPagination) else "/async"

        spec = schema.dict(exclude_none=True)["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]
        assert spec == {
            "media_type_schema": {
                "properties": {
                    "items": {"items": {"ref": "#/components/schemas/Person"}, "type": "array"},
                    "cursor": {
                        "type": "string",
                        "description": "Unique ID, designating the last identifier in the given data set. This value can be used to request the 'next' batch of records.",
                    },
                    "results_per_page": {"type": "integer", "description": "Maximal number of items to send."},
                },
                "type": "object",
            }
        }
