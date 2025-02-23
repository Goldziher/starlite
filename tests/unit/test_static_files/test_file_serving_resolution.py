from __future__ import annotations

import gzip
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING

import brotli
import pytest

from litestar import MediaType, get
from litestar.file_system import FileSystemAdapter
from litestar.static_files import _get_fs_info, create_static_files_router
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from litestar.types import FileSystemProtocol


def test_default_static_files_router(
    tmpdir: Path,
) -> None:
    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    with create_test_client([create_static_files_router(path="/static", directories=[tmpdir])]) as client:
        response = client.get("/static/test.txt")
        assert response.status_code == HTTP_200_OK, response.text
        assert response.text == "content"


@pytest.fixture()
def setup_dirs(tmpdir: Path) -> tuple[Path, Path]:
    paths = []
    for i in range(1, 3):
        root = tmpdir / str(i)
        root.mkdir()
        file_path = root / f"test_{i}.txt"
        file_path.write_text(f"content{i}", "utf-8")
        paths.append(root)

    return paths[0], paths[1]


def test_multiple_static_files_routers(setup_dirs: tuple[Path, Path]) -> None:
    root1, root2 = setup_dirs

    with create_test_client(
        [
            create_static_files_router(path="/static_first", directories=[root1]),
            create_static_files_router(path="/static_second", directories=[root2]),
        ]
    ) as client:
        response = client.get("/static_first/test_1.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content1"

        response = client.get("/static_second/test_2.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content2"


def test_static_files_routers_with_mixed_file_systems(
    file_system: FileSystemProtocol, setup_dirs: tuple[Path, Path]
) -> None:
    root1, root2 = setup_dirs

    with create_test_client(
        [
            create_static_files_router(path="/static_first", directories=[root1], file_system=file_system),
            create_static_files_router(path="/static_second", directories=[root2]),
        ]
    ) as client:
        response = client.get("/static_first/test_1.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content1"

        response = client.get("/static_second/test_2.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content2"


def test_static_files_routers_with_multiple_directories(
    file_system: FileSystemProtocol, setup_dirs: tuple[Path, Path]
) -> None:
    root1, root2 = setup_dirs

    with create_test_client(
        [create_static_files_router(path="/static", directories=[root1, root2], file_system=file_system)]
    ) as client:
        response = client.get("/static/test_1.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content1"

        response = client.get("/static/test_2.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content2"


def test_staticfiles_for_slash_path_regular_mode(tmpdir: Path) -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    with create_test_client([create_static_files_router(path="/", directories=[tmpdir])]) as client:
        response = client.get("/text.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"


def test_staticfiles_for_slash_path_html_mode(
    tmpdir: Path,
) -> None:
    path = tmpdir / "index.html"
    path.write_text("<html></html>", "utf-8")

    with create_test_client([create_static_files_router(path="/", directories=[tmpdir], html_mode=True)]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "<html></html>"


def test_sub_path_under_static_path(
    tmpdir: Path,
) -> None:
    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    @get("/static/sub/{f:str}", media_type=MediaType.TEXT)
    def handler(f: str) -> str:
        return f

    with create_test_client([create_static_files_router(path="/static", directories=[tmpdir]), handler]) as client:
        response = client.get("/static/test.txt")
        assert response.status_code == HTTP_200_OK

        response = client.get("/static/sub/abc")
        assert response.status_code == HTTP_200_OK


def test_static_substring_of_self(
    tmpdir: Path,
) -> None:
    path = tmpdir.mkdir("static_part").mkdir("static") / "test.txt"  # type: ignore[arg-type, func-returns-value]
    path.write_text("content", "utf-8")

    with create_test_client([create_static_files_router(path="/static", directories=[tmpdir])]) as client:
        response = client.get("/static/static_part/static/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"


@pytest.mark.parametrize("extension", ["css", "js", "html", "json"])
def test_static_files_response_mimetype(
    tmpdir: Path,
    extension: str,
) -> None:
    fn = f"test.{extension}"
    path = tmpdir / fn
    path.write_text("content", "utf-8")
    expected_mime_type = mimetypes.guess_type(fn)[0]

    with create_test_client([create_static_files_router(path="/static", directories=[tmpdir])]) as client:
        response = client.get(f"/static/{fn}")
        assert expected_mime_type
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(expected_mime_type)


@pytest.mark.parametrize("extension", ["gz", "br"])
def test_static_files_response_encoding(
    tmp_path: Path,
    extension: str,
) -> None:
    fn = f"test.js.{extension}"
    path = tmp_path / fn
    compressed_data = None
    if extension == "br":
        compressed_data = brotli.compress(b"content")
    elif extension == "gz":
        compressed_data = gzip.compress(b"content")
    path.write_bytes(compressed_data)  # type: ignore[arg-type]
    expected_encoding_type = mimetypes.guess_type(fn)[1]

    with create_test_client([create_static_files_router(path="/static", directories=[tmp_path])]) as client:
        response = client.get(f"/static/{fn}")
        assert expected_encoding_type
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-encoding"].startswith(expected_encoding_type)


@pytest.mark.parametrize("send_as_attachment,disposition", [(True, "attachment"), (False, "inline")])
def test_static_files_content_disposition(
    tmpdir: Path,
    send_as_attachment: bool,
    disposition: str,
) -> None:
    path = tmpdir.mkdir("static_part").mkdir("static") / "test.txt"  # type: ignore[arg-type, func-returns-value]
    path.write_text("content", "utf-8")

    with create_test_client(
        [create_static_files_router(path="/static", directories=[tmpdir], send_as_attachment=send_as_attachment)]
    ) as client:
        response = client.get("/static/static_part/static/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-disposition"].startswith(disposition)


def test_service_from_relative_path_using_string(
    tmpdir: Path,
) -> None:
    sub_dir = Path(tmpdir.mkdir("low")).resolve()  # type: ignore[arg-type, func-returns-value]

    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    with create_test_client([create_static_files_router(path="/static", directories=[f"{sub_dir}/.."])]) as client:
        response = client.get("/static/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"


def test_service_from_relative_path_using_path(
    tmpdir: Path,
) -> None:
    sub_dir = Path(tmpdir.mkdir("low")).resolve()  # type: ignore[arg-type, func-returns-value]

    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    with create_test_client(
        [create_static_files_router(path="/static", directories=[Path(f"{sub_dir}/..")])]
    ) as client:
        response = client.get("/static/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"


@pytest.mark.parametrize("resolve", [True, False])
def test_resolve_symlinks(tmp_path: Path, resolve: bool) -> None:
    source_dir = tmp_path / "foo"
    source_dir.mkdir()
    linked_dir = tmp_path / "bar"
    linked_dir.symlink_to(source_dir, target_is_directory=True)
    source_dir.joinpath("test.txt").write_text("hello")

    router = create_static_files_router(path="/", directories=[linked_dir], resolve_symlinks=resolve)

    with create_test_client(router) as client:
        if not resolve:
            linked_dir.unlink()
            assert client.get("/test.txt").status_code == 404
        else:
            assert client.get("/test.txt").status_code == 200


async def test_staticfiles_get_fs_info_no_access_to_non_static_directory(
    tmp_path: Path,
    file_system: FileSystemProtocol,
) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    index = tmp_path / "index.html"
    index.write_text("content", "utf-8")
    path, info = await _get_fs_info([assets], "../index.html", adapter=FileSystemAdapter(file_system))
    assert path is None
    assert info is None


async def test_staticfiles_get_fs_info_no_access_to_non_static_file_with_prefix(
    tmp_path: Path,
    file_system: FileSystemProtocol,
) -> None:
    static = tmp_path / "static"
    static.mkdir()
    private_file = tmp_path / "staticsecrets.env"
    private_file.write_text("content", "utf-8")
    path, info = await _get_fs_info([static], "../staticsecrets.env", adapter=FileSystemAdapter(file_system))
    assert path is None
    assert info is None
