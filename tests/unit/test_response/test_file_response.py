import os
from datetime import datetime, timezone
from email.utils import formatdate
from os import stat, urandom
from pathlib import Path
from typing import Any, Coroutine

import pytest
from fsspec.implementations.local import LocalFileSystem

from litestar import get
from litestar.connection.base import empty_send
from litestar.datastructures import ETag
from litestar.exceptions import ImproperlyConfiguredException
from litestar.file_system import BaseLocalFileSystem, FileSystemAdapter
from litestar.response.file import ASGIFileResponse, File, async_file_iterator
from litestar.status_codes import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.testing import create_test_client
from litestar.types import FileSystemProtocol

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize("content_disposition_type", ("inline", "attachment"))
def test_file_response_default_content_type(tmpdir: Path, content_disposition_type: Any) -> None:
    path = Path(tmpdir / "image.png")
    path.write_bytes(b"")

    @get("/")
    def handler() -> File:
        return File(path=path, content_disposition_type=content_disposition_type)

    with create_test_client(handler, openapi_config=None) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"] == "application/octet-stream"
        assert response.headers["content-disposition"] == f'{content_disposition_type}; filename=""'


@pytest.mark.parametrize("content_disposition_type", ("inline", "attachment"))
def test_file_response_infer_content_type(tmpdir: Path, content_disposition_type: Any) -> None:
    path = Path(tmpdir / "image.png")
    path.write_bytes(b"")

    @get("/")
    def handler() -> File:
        return File(path=path, filename="image.png", content_disposition_type=content_disposition_type)

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"] == "image/png"
        assert response.headers["content-disposition"] == f'{content_disposition_type}; filename="image.png"'


@pytest.mark.parametrize("filename, expected", (("Jacky Chen", "Jacky%20Chen"), ("成龍", "%E6%88%90%E9%BE%8D")))
def test_filename(tmpdir: Path, filename: str, expected: str) -> None:
    path = Path(tmpdir / f"{filename}.txt")
    path.write_bytes(b"")

    @get("/")
    def handler() -> File:
        return File(path=path, filename=f"{filename}.txt")

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-disposition"] == f"attachment; filename*=utf-8''{expected}.txt"


def test_file_response_content_length(tmpdir: Path) -> None:
    content = urandom(1024 * 10)
    path = Path(tmpdir / "file.txt")
    path.write_bytes(content)

    @get("/")
    def handler() -> File:
        return File(path=path)

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.content == content
        assert response.headers["content-length"] == str(len(content))


def test_file_response_last_modified(tmpdir: Path) -> None:
    path = Path(tmpdir / "file.txt")
    path.write_bytes(b"")

    @get("/")
    def handler() -> File:
        return File(path=path, filename="image.png")

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers["last-modified"].lower() == formatdate(path.stat().st_mtime, usegmt=True).lower()


@pytest.mark.parametrize(
    "mtime,expected_last_modified",
    [
        pytest.param(
            datetime(2000, 1, 2, 3, 4, 5, tzinfo=timezone.utc).timestamp(),
            "Sun, 02 Jan 2000 03:04:05 GMT",
            id="timestamp",
        ),
        pytest.param(
            datetime(2000, 1, 2, 3, 4, 5, tzinfo=timezone.utc), "Sun, 02 Jan 2000 03:04:05 GMT", id="datetime"
        ),
        pytest.param(
            datetime(2000, 1, 2, 3, 4, 5, tzinfo=timezone.utc).isoformat(),
            "Sun, 02 Jan 2000 03:04:05 GMT",
            id="isoformat",
        ),
    ],
)
@pytest.mark.parametrize(
    "mtime_key",
    [
        "mtime",
        "ctime",
        "Last-Modified",
        "updated_at",
        "modification_time",
        "last_changed",
        "change_time",
        "last_modified",
        "last_updated",
        "timestamp",
    ],
)
def test_file_response_last_modified_file_info_formats(
    tmpdir: Path, mtime: Any, mtime_key: str, expected_last_modified: str
) -> None:
    path = Path(tmpdir / "file.txt")
    path.write_bytes(b"")
    file_info = {"name": "file.txt", "size": 0, "type": "file", mtime_key: mtime}

    @get("/")
    def handler() -> File:
        return File(
            path=path,
            filename="image.png",
            file_info=file_info,  # type: ignore[arg-type]
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers["last-modified"].lower() == expected_last_modified.lower()


def test_file_response_last_modified_unsupported_mtime_type(tmpdir: Path) -> None:
    path = Path(tmpdir / "file.txt")
    path.write_bytes(b"")
    file_info = {"name": "file.txt", "size": 0, "type": "file", "last_updated": object()}

    @get("/")
    def handler() -> File:
        return File(
            path=path,
            filename="image.png",
            file_info=file_info,  # type: ignore[arg-type]
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert "last-modified" not in response.headers


def test_file_response_last_modified_mtime_not_given(tmpdir: Path) -> None:
    path = Path(tmpdir / "file.txt")
    path.write_bytes(b"")
    file_info = {"name": "file.txt", "size": 0, "type": "file"}

    @get("/")
    def handler() -> File:
        return File(
            path=path,
            filename="image.png",
            file_info=file_info,  # type: ignore[arg-type]
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert "last-modified" not in response.headers


def test_file_response_etag_without_mtime(tmpdir: Path) -> None:
    path = Path(tmpdir / "file.txt")
    path.write_bytes(b"")
    file_info = {"name": "file.txt", "size": 0, "type": "file"}

    @get("/")
    def handler() -> File:
        return File(
            path=path,
            filename="image.png",
            file_info=file_info,  # type: ignore[arg-type]
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        # we expect etag to only have 2 parts here because no mtime was given
        assert len(response.headers.get("etag", "").split("-")) == 2


async def test_file_response_with_directory_raises_error(tmpdir: Path) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        asgi_response = ASGIFileResponse(file_path=tmpdir, filename="example.png")
        await asgi_response.start_response(empty_send)


@pytest.mark.parametrize("chunk_size", [4, 8, 16, 256, 512, 1024, 2048])
async def test_file_iterator(tmpdir: Path, chunk_size: int) -> None:
    content = urandom(1024)
    path = Path(tmpdir / "file.txt")
    path.write_bytes(content)
    result = b"".join(
        [
            chunk
            async for chunk in async_file_iterator(
                file_path=path, chunk_size=chunk_size, adapter=FileSystemAdapter(BaseLocalFileSystem())
            )
        ]
    )
    assert result == content


@pytest.mark.parametrize("size", (1024, 2048, 4096, 1024 * 10, 2048 * 10, 4096 * 10))
def test_large_files(tmpdir: Path, size: int) -> None:
    content = urandom(1024 * size)
    path = Path(tmpdir / "file.txt")
    path.write_bytes(content)

    @get("/")
    def handler() -> File:
        return File(path=path)

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.content == content
        assert response.headers["content-length"] == str(len(content))


@pytest.mark.parametrize("file_system", (BaseLocalFileSystem(), LocalFileSystem()))
def test_file_with_different_file_systems(tmpdir: "Path", file_system: "FileSystemProtocol") -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    @get("/", media_type="application/octet-stream")
    def handler() -> File:
        return File(
            filename="text.txt",
            path=path,
            file_system=file_system,
        )

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"
        assert response.headers.get("content-disposition") == 'attachment; filename="text.txt"'


def test_file_with_passed_in_file_info(tmpdir: "Path") -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    fs = LocalFileSystem()
    fs_info = fs.info(tmpdir / "text.txt")

    assert fs_info

    @get("/", media_type="application/octet-stream")
    def handler() -> File:
        return File(filename="text.txt", path=path, file_system=fs, file_info=fs_info)  # pyright: ignore

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK, response.text
        assert response.text == "content"
        assert response.headers.get("content-disposition") == 'attachment; filename="text.txt"'


def test_file_with_passed_in_stat_result(tmpdir: "Path") -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    fs = LocalFileSystem()
    stat_result = stat(path)

    @get("/", media_type="application/octet-stream")
    def handler() -> File:
        return File(filename="text.txt", path=path, file_system=fs, stat_result=stat_result)  # pyright: ignore

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"
        assert response.headers.get("content-disposition") == 'attachment; filename="text.txt"'


async def test_file_with_symbolic_link(tmpdir: "Path") -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    linked = tmpdir / "alt.txt"
    os.symlink(path, linked, target_is_directory=False)

    fs = BaseLocalFileSystem()
    file_info = await fs.info(linked)

    assert file_info["islink"]

    @get("/", media_type="application/octet-stream")
    def handler() -> File:
        return File(filename="alt.txt", path=linked, file_system=fs, file_info=file_info)

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"
        assert response.headers.get("content-disposition") == 'attachment; filename="alt.txt"'


async def test_file_sets_etag_correctly(tmpdir: "Path") -> None:
    path = tmpdir / "file.txt"
    content = b"<file content>"
    Path(path).write_bytes(content)
    etag = ETag(value="special")

    @get("/")
    def handler() -> File:
        return File(path=path, etag=etag)

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers["etag"] == '"special"'


def test_file_system_validation(tmpdir: "Path") -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    class FSWithoutOpen:
        def info(self) -> None:
            return

    with pytest.raises(ImproperlyConfiguredException):
        File(
            filename="text.txt",
            path=path,
            file_system=FSWithoutOpen(),  # type:ignore[arg-type]
        )

    class FSWithoutInfo:
        def open(self) -> None:
            return

    with pytest.raises(ImproperlyConfiguredException):
        File(
            filename="text.txt",
            path=path,
            file_system=FSWithoutInfo(),  # type:ignore[arg-type]
        )

    class ImplementedFS:
        def info(self) -> None:
            return

        def open(self) -> None:
            return

    assert File(
        filename="text.txt",
        path=path,
        file_system=ImplementedFS(),  # type:ignore[arg-type]
    )


async def test_file_response_with_missing_file_raises_error(tmpdir: Path) -> None:
    path = tmpdir / "404.txt"
    with pytest.raises(ImproperlyConfiguredException):
        asgi_response = ASGIFileResponse(file_path=path, filename="404.txt")
        await asgi_response.start_response(empty_send)


@pytest.fixture()
def file(tmpdir: Path) -> Path:
    path = tmpdir / "file.txt"
    content = b"a"
    Path(path).write_bytes(content)
    return path


@pytest.mark.parametrize("header_name", ["content-length", "Content-Length", "contenT-leNgTh"])
def test_does_not_override_existing_content_length_header(header_name: str, file: Path) -> None:
    @get("/")
    def handler() -> File:
        return File(path=file, headers={header_name: "2"})

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers.get_list("content-length") == ["2"]


@pytest.mark.parametrize("header_name", ["last-modified", "Last-Modified", "LasT-modiFieD"])
def test_does_not_override_existing_last_modified_header(header_name: str, tmpdir: Path) -> None:
    path = Path(tmpdir / "file.txt")
    path.write_bytes(b"")

    @get("/")
    def handler() -> File:
        return File(path=path, headers={header_name: "foo"})

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers.get_list("last-modified") == ["foo"]


def test_asgi_response_encoded_headers(file: Path) -> None:
    response = ASGIFileResponse(encoded_headers=[(b"foo", b"bar")], file_path=file)
    if isinstance(response.file_info, Coroutine):
        response.file_info.close()  # silence the ResourceWarning
    assert response.encode_headers() == [
        (b"foo", b"bar"),
        (b"content-type", b"application/octet-stream"),
        (b"content-disposition", b'attachment; filename=""'),
    ]
