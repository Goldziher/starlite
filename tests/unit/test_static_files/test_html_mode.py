from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.static_files import create_static_files_router
from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from pathlib import Path

    from litestar.types import FileSystemProtocol


def test_staticfiles_is_html_mode(tmpdir: Path, file_system: FileSystemProtocol) -> None:
    path = tmpdir / "index.html"
    path.write_text("content", "utf-8")

    with create_test_client(
        [create_static_files_router(path="/static", directories=[tmpdir], html_mode=True, file_system=file_system)]
    ) as client:
        response = client.get("/static")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.headers["content-disposition"].startswith("inline")


def test_staticfiles_is_html_mode_serves_404_when_present(tmpdir: Path, file_system: FileSystemProtocol) -> None:
    path = tmpdir / "404.html"
    path.write_text("not found", "utf-8")

    with create_test_client(
        [create_static_files_router(path="/static", directories=[tmpdir], html_mode=True, file_system=file_system)]
    ) as client:
        response = client.get("/static")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.text == "not found"
        assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_staticfiles_is_html_mode_raises_exception_when_no_404_html_is_present(
    tmpdir: Path, file_system: FileSystemProtocol
) -> None:
    with create_test_client(
        [create_static_files_router(path="/static", directories=[tmpdir], html_mode=True, file_system=file_system)]
    ) as client:
        response = client.get("/static")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.json() == {"status_code": 404, "detail": "no file or directory match the path . was found"}
