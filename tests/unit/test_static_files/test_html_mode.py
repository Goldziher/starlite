from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.static_files import StaticFilesConfig
from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from litestar.testing import create_test_client
from tests.unit.test_static_files.conftest import MakeConfig

if TYPE_CHECKING:
    from pathlib import Path

    from litestar.types import FileSystemProtocol


def test_staticfiles_is_html_mode(tmpdir: Path, file_system: FileSystemProtocol, make_config: MakeConfig) -> None:
    path = tmpdir / "index.html"
    path.write_text("content", "utf-8")
    static_files_config, handlers = make_config(
        StaticFilesConfig(path="/static", directories=[tmpdir], html_mode=True, file_system=file_system)
    )

    with create_test_client(handlers, static_files_config=static_files_config) as client:
        response = client.get("/static")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.headers["content-disposition"].startswith("inline")


def test_staticfiles_is_html_mode_serves_404_when_present(
    tmpdir: Path, file_system: FileSystemProtocol, make_config: MakeConfig
) -> None:
    path = tmpdir / "404.html"
    path.write_text("not found", "utf-8")
    static_files_config, handlers = make_config(
        StaticFilesConfig(path="/static", directories=[tmpdir], html_mode=True, file_system=file_system)
    )
    with create_test_client(handlers, static_files_config=static_files_config) as client:
        response = client.get("/static")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.text == "not found"
        assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_staticfiles_is_html_mode_raises_exception_when_no_404_html_is_present(
    tmpdir: Path, file_system: FileSystemProtocol, make_config: MakeConfig
) -> None:
    static_files_config, handlers = make_config(
        StaticFilesConfig(path="/static", directories=[tmpdir], html_mode=True, file_system=file_system)
    )
    with create_test_client(handlers, static_files_config=static_files_config) as client:
        response = client.get("/static")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.json() == {"status_code": 404, "detail": "no file or directory match the path . was found"}
