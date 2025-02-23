from __future__ import annotations

import pytest
from _pytest.fixtures import FixtureRequest
from fsspec.implementations.local import LocalFileSystem

from litestar.file_system import BaseLocalFileSystem
from litestar.types import FileSystemProtocol


@pytest.fixture(params=[BaseLocalFileSystem(), LocalFileSystem()])
def file_system(request: FixtureRequest) -> FileSystemProtocol:
    return request.param  # type: ignore[no-any-return]
