from typing import TYPE_CHECKING, Any, List

import pytest

from litestar import HttpMethod, Litestar, MediaType, get
from litestar.exceptions import ImproperlyConfiguredException
from litestar.static_files import StaticFilesConfig, create_static_files_router
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_405_METHOD_NOT_ALLOWED
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("directories", [[], [""]])
@pytest.mark.parametrize("func", [StaticFilesConfig, create_static_files_router])
def test_config_validation_of_directories(func: Any, directories: List[str]) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        func(path="/static", directories=directories)


@pytest.mark.parametrize("func", [StaticFilesConfig, create_static_files_router])
def test_config_validation_of_path(tmpdir: "Path", func: Any) -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    with pytest.raises(ImproperlyConfiguredException):
        func(path="", directories=[tmpdir])

    with pytest.raises(ImproperlyConfiguredException):
        func(path="/{param:int}", directories=[tmpdir])


@pytest.mark.parametrize("func", [StaticFilesConfig, create_static_files_router])
def test_config_validation_of_file_system(tmpdir: "Path", func: Any) -> None:
    class FSWithoutOpen:
        def info(self) -> None:
            return

    with pytest.raises(ImproperlyConfiguredException):
        func(path="/static", directories=[tmpdir], file_system=FSWithoutOpen())

    class FSWithoutInfo:
        def open(self) -> None:
            return

    with pytest.raises(ImproperlyConfiguredException):
        func(path="/static", directories=[tmpdir], file_system=FSWithoutInfo())

    class ImplementedFS:
        def info(self) -> None:
            return

        def open(self) -> None:
            return

    assert func(path="/static", directories=[tmpdir], file_system=ImplementedFS())


def test_runtime_validation_of_static_path_and_path_parameter(tmpdir: "Path") -> None:
    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    @get("/static/{f:str}", media_type=MediaType.TEXT)
    def handler(f: str) -> str:
        return f

    with pytest.raises(ImproperlyConfiguredException):
        Litestar(
            route_handlers=[handler], static_files_config=[StaticFilesConfig(path="/static", directories=[tmpdir])]
        )


@pytest.mark.parametrize(
    "method, expected",
    (
        (HttpMethod.GET, HTTP_200_OK),
        (HttpMethod.HEAD, HTTP_200_OK),
        (HttpMethod.PUT, HTTP_405_METHOD_NOT_ALLOWED),
        (HttpMethod.PATCH, HTTP_405_METHOD_NOT_ALLOWED),
        (HttpMethod.POST, HTTP_405_METHOD_NOT_ALLOWED),
        (HttpMethod.DELETE, HTTP_405_METHOD_NOT_ALLOWED),
        (HttpMethod.OPTIONS, HTTP_405_METHOD_NOT_ALLOWED),
    ),
)
def test_runtime_validation_of_request_method_legacy_config(tmpdir: "Path", method: HttpMethod, expected: int) -> None:
    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    with create_test_client(
        [], static_files_config=[StaticFilesConfig(path="/static", directories=[tmpdir])]
    ) as client:
        response = client.request(method, "/static/test.txt")
        assert response.status_code == expected


@pytest.mark.parametrize(
    "method, expected",
    (
        (HttpMethod.GET, HTTP_200_OK),
        (HttpMethod.HEAD, HTTP_200_OK),
        (HttpMethod.OPTIONS, HTTP_204_NO_CONTENT),
        (HttpMethod.PUT, HTTP_405_METHOD_NOT_ALLOWED),
        (HttpMethod.PATCH, HTTP_405_METHOD_NOT_ALLOWED),
        (HttpMethod.POST, HTTP_405_METHOD_NOT_ALLOWED),
        (HttpMethod.DELETE, HTTP_405_METHOD_NOT_ALLOWED),
    ),
)
def test_runtime_validation_of_request_method_create_handler(tmpdir: "Path", method: HttpMethod, expected: int) -> None:
    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    with create_test_client(create_static_files_router(path="/static", directories=[tmpdir])) as client:
        response = client.request(method, "/static/test.txt")
        assert response.status_code == expected
