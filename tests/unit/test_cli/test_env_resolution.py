from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from click import ClickException

from litestar import Litestar
from litestar.cli._utils import LitestarEnv, _path_to_dotted_path

from .conftest import CreateAppFileFixture

pytestmark = pytest.mark.xdist_group("cli_autodiscovery")


def test_litestar_env_from_env_port(monkeypatch: MonkeyPatch, app_file: Path) -> None:
    env = LitestarEnv.from_env(f"{app_file.stem}:app")
    assert env.port is None

    monkeypatch.setenv("LITESTAR_PORT", "7000")
    env = LitestarEnv.from_env(f"{app_file.stem}:app")
    assert env.port == 7000


def test_litestar_env_from_env_host(monkeypatch: MonkeyPatch, app_file: Path) -> None:
    env = LitestarEnv.from_env(f"{app_file.stem}:app")
    assert env.host is None

    monkeypatch.setenv("LITESTAR_HOST", "0.0.0.0")
    env = LitestarEnv.from_env(f"{app_file.stem}:app")
    assert env.host == "0.0.0.0"


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("app.py", id="app_file"),
        pytest.param("application.py", id="application_file"),
        pytest.param("app/main.py", id="app_module"),
        pytest.param("app/any_name.py", id="app_module_random"),
        pytest.param("application/another_random_name.py", id="application_module_random"),
    ],
)
def test_env_from_env_autodiscover_from_files(
    path: str, app_file_content: str, app_file_app_name: str, create_app_file: CreateAppFileFixture
) -> None:
    directory = None
    if "/" in path:
        directory, path = path.split("/", 1)

    tmp_file_path = create_app_file(file=path, directory=directory, content=app_file_content)
    env = LitestarEnv.from_env(None)

    dotted_path = _path_to_dotted_path(tmp_file_path.relative_to(Path.cwd()))

    assert isinstance(env.app, Litestar)

    print("parent directory content: %s", list(tmp_file_path.parent.iterdir()))  # noqa: T201
    assert env.app_path == f"{dotted_path}:{app_file_app_name}"


@pytest.mark.parametrize(
    "module_name,app_file",
    [
        ("app", "main.py"),
        ("application", "main.py"),
        ("app", "anything.py"),
        ("application", "anything.py"),
    ],
)
def test_env_from_env_autodiscover_from_module(
    module_name: str,
    app_file: str,
    app_file_content: str,
    app_file_app_name: str,
    create_app_file: CreateAppFileFixture,
) -> None:
    create_app_file(
        file=app_file,
        directory=module_name,
        content=app_file_content,
        init_content=f"from .{app_file.split('.')[0]} import {app_file_app_name}",
    )
    env = LitestarEnv.from_env(None)

    assert isinstance(env.app, Litestar)
    assert env.app_path == f"{module_name}:{app_file_app_name}"


@pytest.mark.parametrize("path", [".app.py", "_app.py", ".application.py", "_application.py"])
def test_env_from_env_autodiscover_from_files_ignore_paths(
    path: str, app_file_content: str, create_app_file: CreateAppFileFixture
) -> None:
    create_app_file(file=path, directory=None, content=app_file_content)

    with pytest.raises(ClickException):
        LitestarEnv.from_env(None)


@pytest.mark.parametrize("use_file_in_app_path", [True, False])
def test_env_using_app_dir(
    app_file_content: str, app_file_app_name: str, create_app_file: CreateAppFileFixture, use_file_in_app_path: bool
) -> None:
    app_file = "main.py"
    app_file_without_extension = app_file.split(".")[0]
    tmp_file_path = create_app_file(
        file=app_file,
        directory="src",
        content=app_file_content,
        subdir=f"litestar_test_{app_file_app_name}",
        init_content=f"from .{app_file_without_extension} import {app_file_app_name}",
    )
    app_path_components = [f"litestar_test_{app_file_app_name}"]
    if use_file_in_app_path:
        app_path_components.append(app_file_without_extension)

    app_path = f"{'.'.join(app_path_components)}:{app_file_app_name}"
    env = LitestarEnv.from_env(app_path, app_dir=Path().cwd() / "src")

    dotted_path = _path_to_dotted_path(tmp_file_path.relative_to(Path.cwd()))

    assert isinstance(env.app, Litestar)
    dotted_path = dotted_path.replace("src.", "")
    if not use_file_in_app_path:
        dotted_path = dotted_path.replace(".main", "")
    assert env.app_path == f"{dotted_path}:{app_file_app_name}"
