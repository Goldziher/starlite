from __future__ import annotations

from dataclasses import asdict
from typing import Callable

import pytest
from _pytest.fixtures import FixtureRequest
from fsspec.implementations.local import LocalFileSystem
from typing_extensions import TypeAlias

from litestar import Router
from litestar.file_system import BaseLocalFileSystem
from litestar.static_files import StaticFilesConfig, create_static_files_router
from litestar.types import FileSystemProtocol

MakeConfig: TypeAlias = "Callable[[StaticFilesConfig], tuple[list[StaticFilesConfig], list[Router]]]"


@pytest.fixture(params=["config", "handlers"])
def make_config(request: FixtureRequest) -> MakeConfig:
    def make(config: StaticFilesConfig) -> tuple[list[StaticFilesConfig], list[Router]]:
        if request.param == "config":
            return [config], []
        return [], [create_static_files_router(**asdict(config))]

    return make


@pytest.fixture(params=[BaseLocalFileSystem(), LocalFileSystem()])
def file_system(request: FixtureRequest) -> FileSystemProtocol:
    return request.param  # type: ignore[no-any-return]
