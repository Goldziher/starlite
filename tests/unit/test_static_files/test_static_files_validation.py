from pathlib import Path

import pytest

from litestar import HttpMethod
from litestar.exceptions import ImproperlyConfiguredException
from litestar.static_files import create_static_files_router
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_405_METHOD_NOT_ALLOWED
from litestar.testing import create_test_client


@pytest.mark.parametrize("directories", [[], [""]])
def test_validation_of_directories(directories: list[str]) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        create_static_files_router(path="/static", directories=[])


def test_validation_of_path(tmpdir: "Path") -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    with pytest.raises(ImproperlyConfiguredException):
        create_static_files_router(path="", directories=[tmpdir])

    with pytest.raises(ImproperlyConfiguredException):
        create_static_files_router(path="/{param:int}", directories=[tmpdir])


def test_validation_of_file_system(tmpdir: "Path") -> None:
    class FSWithoutOpen:
        def info(self) -> None:
            return

    with pytest.raises(ImproperlyConfiguredException):
        create_static_files_router(path="/static", directories=[tmpdir], file_system=FSWithoutOpen())

    class FSWithoutInfo:
        def open(self) -> None:
            return

    with pytest.raises(ImproperlyConfiguredException):
        create_static_files_router(path="/static", directories=[tmpdir], file_system=FSWithoutInfo())

    class ImplementedFS:
        def info(self) -> None:
            return

        def open(self) -> None:
            return

    assert create_static_files_router(path="/static", directories=[tmpdir], file_system=ImplementedFS())


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
