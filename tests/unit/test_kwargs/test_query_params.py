from datetime import datetime
from typing import (
    Annotated,
    Any,
    Optional,
    Union,
)
from urllib.parse import urlencode

import pytest

from litestar import MediaType, Request, get, post
from litestar.datastructures import MultiDict
from litestar.di import Provide
from litestar.params import Parameter
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client


@pytest.mark.parametrize(
    "params_dict,should_raise",
    [
        (
            {
                "page": 1,
                "pageSize": 1,
                "brands": ["Nike", "Adidas"],
            },
            False,
        ),
        (
            {
                "page": 1,
                "pageSize": 1,
                "brands": ["Nike", "Adidas", "Rebok"],
            },
            False,
        ),
        (
            {
                "page": 1,
                "pageSize": 1,
            },
            True,
        ),
        (
            {
                "page": 1,
                "pageSize": 1,
                "brands": ["Nike", "Adidas", "Rebok", "Polgat"],
            },
            True,
        ),
        (
            {
                "page": 1,
                "pageSize": 101,
                "brands": ["Nike", "Adidas", "Rebok"],
            },
            True,
        ),
        (
            {
                "page": 1,
                "pageSize": 1,
                "brands": [],
            },
            True,
        ),
        (
            {
                "page": 1,
                "pageSize": 1,
                "brands": ["Nike", "Adidas", "Rebok"],
                "from_date": datetime.now().timestamp(),
            },
            False,
        ),
        (
            {
                "page": 1,
                "pageSize": 1,
                "brands": ["Nike", "Adidas", "Rebok"],
                "from_date": datetime.now().timestamp(),
                "to_date": datetime.now().timestamp(),
            },
            False,
        ),
        (
            {
                "page": 1,
                "pageSize": 1,
                "brands": ["Nike"],
                "from_date": datetime.now().timestamp(),
                "to_date": datetime.now().timestamp(),
            },
            False,
        ),
    ],
)
def test_query_params(params_dict: dict, should_raise: bool) -> None:
    test_path = "/test"

    @get(path=test_path)
    def test_method(
        page: int,
        page_size: int = Parameter(query="pageSize", gt=0, le=100),
        brands: list[str] = Parameter(min_items=1, max_items=3),
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> None:
        assert page
        assert page_size
        assert brands
        assert from_date or from_date is None
        assert to_date or to_date is None

    with create_test_client(test_method) as client:
        response = client.get(f"{test_path}?{urlencode(params_dict, doseq=True)}")
        if should_raise:
            assert response.status_code == HTTP_400_BAD_REQUEST, response.json()
        else:
            assert response.status_code == HTTP_200_OK, response.json()


@pytest.mark.parametrize(
    "expected_type,provided_value,default,expected_response_code",
    [
        (Union[int, list[int]], [1, 2, 3], None, HTTP_200_OK),
        (Union[int, list[int]], [1], None, HTTP_200_OK),
    ],
)
def test_query_param_arrays(expected_type: Any, provided_value: Any, default: Any, expected_response_code: int) -> None:
    test_path = "/test"

    @get(test_path)
    def test_method_with_default(param: Any = default) -> None:
        return None

    @get(test_path)
    def test_method_without_default(param: Any) -> None:
        return None

    test_method = test_method_without_default if default is ... else test_method_with_default
    # Set the type annotation of 'param' in a way mypy can deal with
    test_method.fn.__annotations__["param"] = expected_type

    with create_test_client(test_method) as client:
        params = urlencode({"param": provided_value}, doseq=True)
        response = client.get(f"{test_path}?{params}")
        assert response.status_code == expected_response_code


def test_query_kwarg() -> None:
    test_path = "/test"

    params = urlencode(
        {
            "a": ["foo", "bar"],
            "b": "qux",
        },
        doseq=True,
    )

    @get(test_path)
    def handler(a: list[str], b: list[str], query: MultiDict) -> None:
        assert isinstance(query, MultiDict)
        assert {k: query.getall(k) for k in query} == {"a": ["foo", "bar"], "b": ["qux"]}
        assert isinstance(a, list)
        assert isinstance(b, list)
        assert a == ["foo", "bar"]
        assert b == ["qux"]

    with create_test_client(handler) as client:
        response = client.get(f"{test_path}?{params}")
        assert response.status_code == HTTP_200_OK, response.json()


@pytest.mark.parametrize(
    "values",
    (
        (("first", "x@test.com"), ("second", "aaa")),
        (("first", "&@A.ac"), ("second", "aaa")),
        (("first", "a@A.ac&"), ("second", "aaa")),
        (("first", "a@A&.ac"), ("second", "aaa")),
    ),
)
def test_query_parsing_of_escaped_values(values: tuple[tuple[str, str], tuple[str, str]]) -> None:
    # https://github.com/litestar-org/litestar/issues/915

    request_values: dict[str, Any] = {}

    @get(path="/handler")
    def handler(request: Request, first: str, second: str) -> None:
        request_values["first"] = first
        request_values["second"] = second
        request_values["query"] = request.query_params

    params = dict(values)

    with create_test_client(handler) as client:
        response = client.get("/handler", params=params)
        assert response.status_code == HTTP_200_OK
        assert request_values["first"] == params["first"]
        assert request_values["second"] == params["second"]
        assert request_values["query"].get("first") == params["first"]
        assert request_values["query"].get("second") == params["second"]


def test_query_param_dependency_with_alias() -> None:
    async def qp_dependency(page_size: int = Parameter(query="pageSize", gt=0, le=100)) -> int:
        return page_size

    @get("/", media_type=MediaType.TEXT)
    def handler(page_size_dep: int) -> str:
        return str(page_size_dep)

    with create_test_client(handler, dependencies={"page_size_dep": Provide(qp_dependency)}) as client:
        response = client.get("/?pageSize=1")
        assert response.status_code == HTTP_200_OK, response.text
        assert response.text == "1"


def test_query_params_with_post() -> None:
    # https://github.com/litestar-org/litestar/issues/3734
    @post()
    async def handler(data: str, secret: Annotated[str, Parameter(query="x-secret")]) -> None:
        return None

    with create_test_client([handler], raise_server_exceptions=True) as client:
        assert client.post("/", json={}).status_code == 400
