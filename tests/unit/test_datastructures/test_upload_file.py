from os import urandom
from pathlib import Path
from typing import Optional

import pytest

from litestar import post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.status_codes import HTTP_201_CREATED
from litestar.testing import create_test_client

pytestmark = pytest.mark.anyio


async def test_upload_file_methods() -> None:
    data = urandom(5)
    upload_file = UploadFile(content_type="application/text", filename="tmp.txt", max_spool_size=10, file_data=data)

    assert repr(upload_file) == "tmp.txt - application/text"
    assert not upload_file.rolled_to_disk

    assert await upload_file.read() == data
    assert await upload_file.read() == b""
    await upload_file.seek(0)
    assert await upload_file.read() == data

    await upload_file.write(b"extra_data")

    assert upload_file.rolled_to_disk

    await upload_file.seek(5)  # type: ignore[unreachable]
    assert await upload_file.read() == b"extra_data"

    await upload_file.write(b"writing_async_extra_data")

    await upload_file.seek(15)
    assert await upload_file.read() == b"writing_async_extra_data"

    await upload_file.close()
    assert upload_file.file.closed


def test_cleanup_is_being_performed(tmpdir: Path) -> None:
    path1 = tmpdir / "test.txt"
    Path(path1).write_bytes(b"<file content>")

    upload_file: Optional[UploadFile] = None

    @post("/form", sync_to_thread=False)
    def handler(data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART)) -> None:
        nonlocal upload_file
        upload_file = data
        assert not upload_file.file.closed

    with create_test_client(handler) as client, open(path1, "rb") as f:
        response = client.post("/form", files={"test": ("test.txt", f, "text/plain")})
        assert response.status_code == HTTP_201_CREATED
        assert upload_file
        assert upload_file.file.closed
