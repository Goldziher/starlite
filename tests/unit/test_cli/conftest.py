from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Callable, Generator, Protocol, cast

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner
from pytest_mock import MockerFixture

from litestar.cli._utils import _path_to_dotted_path

from . import (
    APP_FILE_CONTENT,
    CREATE_APP_FILE_CONTENT,
    GENERIC_APP_FACTORY_FILE_CONTENT,
    GENERIC_APP_FACTORY_FILE_CONTENT_FUTURE_ANNOTATIONS,
    GENERIC_APP_FACTORY_FILE_CONTENT_STRING_ANNOTATION,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from litestar.cli._utils import LitestarGroup


@pytest.fixture(autouse=True)
def reset_litestar_app_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("LITESTAR_APP", raising=False)


@pytest.fixture()
def root_command() -> LitestarGroup:
    import litestar.cli.main

    return cast("LitestarGroup", importlib.reload(litestar.cli.main).litestar_group)


@pytest.fixture
def patch_autodiscovery_paths(request: FixtureRequest) -> Callable[[list[str]], None]:
    def patcher(paths: list[str]) -> None:
        from litestar.cli._utils import AUTODISCOVERY_FILE_NAMES

        old_paths = AUTODISCOVERY_FILE_NAMES[::]
        AUTODISCOVERY_FILE_NAMES[:] = paths

        def finalizer() -> None:
            AUTODISCOVERY_FILE_NAMES[:] = old_paths

        request.addfinalizer(finalizer)

    return patcher


@pytest.fixture
def tmp_project_dir(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    path = tmp_path / "project_dir"
    path.mkdir(exist_ok=True)
    monkeypatch.chdir(path)
    return path


class CreateAppFileFixture(Protocol):
    def __call__(
        self,
        file: str | Path,
        directory: str | Path | None = None,
        content: str | None = None,
        init_content: str = "",
        subdir: str | None = None,
    ) -> Path: ...


def _purge_module(module_names: list[str], path: str | Path) -> None:
    for name in module_names:
        if name in sys.modules:
            del sys.modules[name]
    Path(importlib.util.cache_from_source(path)).unlink(missing_ok=True)  # type: ignore[arg-type]


@pytest.fixture
def create_app_file(tmp_project_dir: Path, request: FixtureRequest) -> CreateAppFileFixture:
    def _create_app_file(
        file: str | Path,
        directory: str | Path | None = None,
        content: str | None = None,
        init_content: str = "",
        subdir: str | None = None,
    ) -> Path:
        base = tmp_project_dir
        if directory:
            base /= Path(Path(directory) / subdir) if subdir else Path(directory)
            base.mkdir(parents=True)
            base.joinpath("__init__.py").write_text(init_content)

        tmp_app_file = base / file
        tmp_app_file.write_text(content or APP_FILE_CONTENT)

        if directory:
            request.addfinalizer(lambda: rmtree(directory))
            request.addfinalizer(
                lambda: _purge_module(
                    [directory, _path_to_dotted_path(tmp_app_file.relative_to(Path.cwd()))],  # type: ignore[list-item]
                    tmp_app_file,
                )
            )
        else:
            request.addfinalizer(tmp_app_file.unlink)
            request.addfinalizer(lambda: _purge_module([str(file).replace(".py", "")], tmp_app_file))
        return tmp_app_file

    return _create_app_file


@pytest.fixture
def app_file(create_app_file: CreateAppFileFixture) -> Path:
    return create_app_file("app.py")


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_uvicorn_run(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("uvicorn.run")


@pytest.fixture()
def mock_subprocess_run(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("subprocess.run")


@pytest.fixture
def mock_confirm_ask(mocker: MockerFixture) -> Generator[MagicMock, None, None]:
    yield mocker.patch("rich.prompt.Confirm.ask", return_value=True)


@pytest.fixture(
    params=[
        pytest.param((APP_FILE_CONTENT, "app"), id="app_obj"),
        pytest.param((CREATE_APP_FILE_CONTENT, "create_app"), id="create_app"),
        pytest.param((GENERIC_APP_FACTORY_FILE_CONTENT, "any_name"), id="app_factory"),
        pytest.param((GENERIC_APP_FACTORY_FILE_CONTENT_STRING_ANNOTATION, "any_name"), id="app_factory_str_annot"),
        pytest.param((GENERIC_APP_FACTORY_FILE_CONTENT_FUTURE_ANNOTATIONS, "any_name"), id="app_factory_future_annot"),
    ]
)
def _app_file_content(request: FixtureRequest) -> tuple[str, str]:
    return cast("tuple[str, str]", request.param)


@pytest.fixture
def app_file_content(_app_file_content: tuple[str, str]) -> str:
    return _app_file_content[0]


@pytest.fixture
def app_file_app_name(_app_file_content: tuple[str, str]) -> str:
    return _app_file_content[1]
