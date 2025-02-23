from collections.abc import Generator
from typing import Annotated, Any, Optional

import pytest

from litestar import Controller, Litestar, MediaType, get, post
from litestar.di import Provide
from litestar.exceptions import ImproperlyConfiguredException
from litestar.params import Body, Dependency, Parameter
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.testing import TestClient, create_test_client


def test_parsing_of_parameter_as_annotated() -> None:
    @get(path="/")
    def handler(param: Annotated[str, Parameter(min_length=1)]) -> str:
        return param

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_400_BAD_REQUEST

        response = client.get("/?param=a")
        assert response.status_code == HTTP_200_OK


def test_parsing_of_parameter_as_default() -> None:
    @get(path="/")
    def handler(param: str = Parameter(min_length=1)) -> str:
        return param

    with create_test_client(handler) as client:
        response = client.get("/?param=")
        assert response.status_code == HTTP_400_BAD_REQUEST

        response = client.get("/?param=a")
        assert response.status_code == HTTP_200_OK


def test_parsing_of_body_as_annotated() -> None:
    @post(path="/")
    def handler(data: Annotated[list[str], Body(min_items=1)]) -> list[str]:
        return data

    with create_test_client(handler) as client:
        response = client.post("/", json=[])
        assert response.status_code == HTTP_400_BAD_REQUEST

        response = client.post("/", json=["a"])
        assert response.status_code == HTTP_201_CREATED


def test_parsing_of_body_as_default() -> None:
    @post(path="/")
    def handler(data: list[str] = Body(min_items=1)) -> list[str]:
        return data

    with create_test_client(handler) as client:
        response = client.post("/", json=[])
        assert response.status_code == HTTP_400_BAD_REQUEST

        response = client.post("/", json=["a"])
        assert response.status_code == HTTP_201_CREATED


def test_parsing_of_dependency_as_annotated() -> None:
    @get(path="/", dependencies={"dep": Provide(lambda: None, sync_to_thread=False)})
    def handler(dep: Annotated[int, Dependency(skip_validation=True)]) -> int:
        return dep

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.text == "null"


def test_parsing_of_dependency_as_default() -> None:
    @get(path="/", dependencies={"dep": Provide(lambda: None, sync_to_thread=False)})
    def handler(dep: int = Dependency(skip_validation=True)) -> int:
        return dep

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.text == "null"


@pytest.mark.parametrize(("default",), [(None,), (13,)])
def test_dependency_defaults(default: Any) -> None:
    @get("/")
    def handler(
        value_1: Optional[int] = Dependency(default=default), value_2: Annotated[Optional[int], Dependency()] = default
    ) -> dict[str, Optional[int]]:
        return {"value_1": value_1, "value_2": value_2}

    with create_test_client(route_handlers=[handler]) as client:
        resp = client.get("/")
        assert resp.json() == {"value_1": default, "value_2": default}


def test_dependency_non_optional_with_default() -> None:
    @get("/")
    def handler(value: int = Dependency(default=13)) -> dict[str, int]:
        return {"value": value}

    with create_test_client(route_handlers=[handler]) as client:
        resp = client.get("/")
        assert resp.json() == {"value": 13}


def test_dependency_no_default() -> None:
    @get(dependencies={"value": Provide(lambda: 13, sync_to_thread=False)})
    def test(value: int = Dependency()) -> dict[str, int]:
        return {"value": value}

    with create_test_client(route_handlers=[test]) as client:
        resp = client.get("/")
    assert resp.json() == {"value": 13}


def test_dependency_not_provided_and_no_default() -> None:
    @get()
    def test(value: int = Dependency()) -> dict[str, int]:
        return {"value": value}

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(route_handlers=[test])


def test_dependency_provided_on_controller() -> None:
    """Ensures that we don't only consider the handler's dependencies when checking that an explicit non-optional
    dependency has been provided.
    """

    class C(Controller):
        path = ""
        dependencies = {"value": Provide(lambda: 13, sync_to_thread=False)}

        @get()
        def test(self, value: int = Dependency()) -> dict[str, int]:
            return {"value": value}

    with create_test_client(route_handlers=[C]) as client:
        resp = client.get("/")
    assert resp.json() == {"value": 13}


def test_dependency_skip_validation() -> None:
    @get("/validated")
    def validated(value: int = Dependency()) -> dict[str, int]:
        return {"value": value}

    @get("/skipped")
    def skipped(value: int = Dependency(skip_validation=True)) -> dict[str, int]:
        return {"value": value}

    with create_test_client(
        route_handlers=[validated, skipped], dependencies={"value": Provide(lambda: "str", sync_to_thread=False)}
    ) as client:
        validated_resp = client.get("/validated")
        assert validated_resp.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        skipped_resp = client.get("/skipped")
        assert skipped_resp.status_code == HTTP_200_OK
        assert skipped_resp.json() == {"value": "str"}


def test_dependency_skip_validation_with_default() -> None:
    @get("/skipped")
    def skipped(value: int = Dependency(default=1, skip_validation=True)) -> dict[str, int]:
        return {"value": value}

    with create_test_client(route_handlers=[skipped]) as client:
        skipped_resp = client.get("/skipped")
        assert skipped_resp.status_code == HTTP_200_OK
        assert skipped_resp.json() == {"value": 1}


def test_dependency_nested_sequence() -> None:
    class Obj:
        def __init__(self, seq: list[str]) -> None:
            self.seq = seq

    async def provides_obj(seq: list[str]) -> Obj:
        return Obj(seq)

    @get("/obj")
    def get_obj(obj: Obj) -> list[str]:
        return obj.seq

    @get("/seq")
    def get_seq(seq: list[str]) -> list[str]:
        return seq

    with create_test_client(
        route_handlers=[get_obj, get_seq],
        dependencies={"obj": Provide(provides_obj)},
    ) as client:
        seq = ["a", "b", "c"]
        resp = client.get("/seq", params={"seq": seq})
        assert resp.json() == ["a", "b", "c"]
        resp = client.get("/obj", params={"seq": seq})
        assert resp.json() == ["a", "b", "c"]


def test_regex_validation() -> None:
    # https://github.com/litestar-org/litestar/issues/1860
    @get(path="/val_regex", media_type=MediaType.TEXT)
    async def regex_val(text: Annotated[str, Parameter(title="a or b", pattern="[a|b]")]) -> str:
        return f"str: {text}"

    with create_test_client(route_handlers=[regex_val]) as client:
        for letter in ("a", "b"):
            response = client.get(f"/val_regex?text={letter}")
            assert response.status_code == HTTP_200_OK
            assert response.text == f"str: {letter}"

        response = client.get("/val_regex?text=c")
        assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.fixture(name="optional_no_default_client")
def optional_no_default_client_fixture() -> Generator[TestClient, None, None]:
    @get("/optional-no-default")
    def handle_optional(key: Optional[str]) -> dict[str, Optional[str]]:
        return {"key": key}

    @get("/optional-annotated-no-default")
    def handle_optional_annotated(param: Annotated[Optional[str], Parameter(query="key")]) -> dict[str, Optional[str]]:
        return {"key": param}

    with create_test_client(route_handlers=[handle_optional, handle_optional_annotated], openapi_config=None) as client:
        yield client


def test_optional_query_parameter_consistency_no_default_queried_without_param(
    optional_no_default_client: TestClient,
) -> None:
    assert optional_no_default_client.get("/optional-no-default", params={}).status_code == HTTP_400_BAD_REQUEST
    assert (
        optional_no_default_client.get("/optional-annotated-no-default", params={}).status_code == HTTP_400_BAD_REQUEST
    )


def test_optional_query_parameter_consistency_no_default_queried_with_expected_param(
    optional_no_default_client: TestClient,
) -> None:
    assert optional_no_default_client.get("/optional-no-default", params={"key": "a"}).json() == {"key": "a"}
    assert optional_no_default_client.get("/optional-annotated-no-default", params={"key": "a"}).json() == {"key": "a"}


def test_optional_query_parameter_consistency_no_default_queried_with_other_param(
    optional_no_default_client: TestClient,
) -> None:
    assert (
        optional_no_default_client.get("/optional-no-default", params={"param": "a"}).status_code
        == HTTP_400_BAD_REQUEST
    )
    assert (
        optional_no_default_client.get("/optional-annotated-no-default", params={"param": "a"}).status_code
        == HTTP_400_BAD_REQUEST
    )


@pytest.fixture(name="optional_default_client")
def optional_default_client_fixture() -> Generator[TestClient, None, None]:
    @get("/optional-default")
    def handle_default(key: Optional[str] = None) -> dict[str, Optional[str]]:
        return {"key": key}

    @get("/optional-annotated-default")
    def handle_default_annotated(
        param: Annotated[Optional[str], Parameter(query="key")] = None,
    ) -> dict[str, Optional[str]]:
        return {"key": param}

    with create_test_client(route_handlers=[handle_default, handle_default_annotated], openapi_config=None) as client:
        yield client


def test_optional_query_parameter_consistency_wiht_default_queried_without_param(
    optional_default_client: TestClient,
) -> None:
    assert optional_default_client.get("/optional-default", params={}).json() == {"key": None}
    assert optional_default_client.get("/optional-annotated-default", params={}).json() == {"key": None}


def test_optional_query_parameter_consistency_with_default_queried_with_expected_param(
    optional_default_client: TestClient,
) -> None:
    assert optional_default_client.get("/optional-default", params={"key": "a"}).json() == {"key": "a"}
    assert optional_default_client.get("/optional-annotated-default", params={"key": "a"}).json() == {"key": "a"}


def test_optional_query_parameter_consistency_with_default_queried_with_other_param(
    optional_default_client: TestClient,
) -> None:
    assert optional_default_client.get("/optional-default", params={"param": "a"}).json() == {"key": None}
    assert optional_default_client.get("/optional-annotated-default", params={"abc": "xyz"}).json() == {"key": None}
    assert optional_default_client.get("/optional-annotated-default", params={"param": "a"}).json() == {"key": None}
