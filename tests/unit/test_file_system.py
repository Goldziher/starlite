import sys
from pathlib import Path
from stat import S_IRWXO
from typing import TYPE_CHECKING

import pytest
from fsspec.implementations.local import LocalFileSystem

from litestar.exceptions import InternalServerException, NotAuthorizedException
from litestar.file_system import BaseLocalFileSystem, FileSystemAdapter

if TYPE_CHECKING:
    from litestar.types import FileSystemProtocol

pytestmark = pytest.mark.anyio


pytestmark = pytest.mark.anyio


@pytest.mark.parametrize("file_system", (BaseLocalFileSystem(), LocalFileSystem()))
async def test_file_adapter_open(tmpdir: Path, file_system: "FileSystemProtocol") -> None:
    file = Path(tmpdir / "test.txt")
    file.write_bytes(b"test")
    adapter = FileSystemAdapter(file_system=file_system)

    async with await adapter.open(file=file) as opened_file:
        assert await opened_file.read() == b"test"


@pytest.mark.parametrize("file_system", (BaseLocalFileSystem(), LocalFileSystem()))
@pytest.mark.xfail(sys.platform == "win32", reason="permissions equivalent missing on windows")
async def test_file_adapter_open_handles_permission_exception(tmpdir: Path, file_system: "FileSystemProtocol") -> None:
    file = Path(tmpdir / "test.txt")
    file.write_bytes(b"test")

    owner_permissions = file.stat().st_mode
    file.chmod(S_IRWXO)
    adapter = FileSystemAdapter(file_system=file_system)

    with pytest.raises(NotAuthorizedException):
        async with await adapter.open(file=file):
            pass

    Path(tmpdir).chmod(owner_permissions)


@pytest.mark.parametrize("file_system", (BaseLocalFileSystem(), LocalFileSystem()))
async def test_file_adapter_open_handles_file_not_found_exception(file_system: "FileSystemProtocol") -> None:
    adapter = FileSystemAdapter(file_system=file_system)

    with pytest.raises(InternalServerException):
        async with await adapter.open(file="non_existing_file.txt"):
            pass


@pytest.mark.parametrize("file_system", (BaseLocalFileSystem(), LocalFileSystem()))
@pytest.mark.xfail(sys.platform == "win32", reason="Suspected fsspec issue", strict=False)
async def test_file_adapter_info(tmpdir: Path, file_system: "FileSystemProtocol") -> None:
    file = Path(tmpdir / "test.txt")
    file.write_bytes(b"test")
    adapter = FileSystemAdapter(file_system=file_system)

    result = file.stat()

    assert await adapter.info(file) == {
        "gid": result.st_gid,
        "ino": result.st_ino,
        "islink": False,
        "mode": result.st_mode,
        "mtime": result.st_mtime,
        "name": str(file),
        "nlink": 1,
        "created": result.st_ctime,
        "size": result.st_size,
        "type": "file",
        "uid": result.st_uid,
    }


@pytest.mark.parametrize("file_system", (BaseLocalFileSystem(), LocalFileSystem()))
async def test_file_adapter_info_handles_file_not_found_exception(file_system: "FileSystemProtocol") -> None:
    adapter = FileSystemAdapter(file_system=file_system)

    with pytest.raises(FileNotFoundError):
        await adapter.info(path="non_existing_file.txt")


@pytest.mark.parametrize("file_system", (BaseLocalFileSystem(), LocalFileSystem()))
@pytest.mark.xfail(sys.platform == "win32", reason="permissions equivalent missing on windows")
async def test_file_adapter_info_handles_permission_exception(tmpdir: Path, file_system: "FileSystemProtocol") -> None:
    file = Path(tmpdir / "test.txt")
    file.write_bytes(b"test")

    owner_permissions = file.stat().st_mode
    Path(tmpdir).chmod(S_IRWXO)
    adapter = FileSystemAdapter(file_system=file_system)

    with pytest.raises(NotAuthorizedException):
        await adapter.info(path=file)

    Path(tmpdir).chmod(owner_permissions)
