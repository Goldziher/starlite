import io
import os
import re
import sys
from pathlib import Path
from typing import Callable, Generator, List, Literal, Optional, Tuple, Union
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner
from pytest_mock import MockerFixture
from rich.console import Console

from litestar import __version__ as litestar_version
from litestar.cli import _utils
from litestar.cli.commands import core
from litestar.cli.main import litestar_group as cli_command
from litestar.exceptions import LitestarWarning

from . import (
    APP_FACTORY_FILE_CONTENT_SERVER_LIFESPAN_PLUGIN,
    APP_FILE_CONTENT_ROUTES_EXAMPLE,
    CREATE_APP_FILE_CONTENT,
    GENERIC_APP_FACTORY_FILE_CONTENT,
    GENERIC_APP_FACTORY_FILE_CONTENT_STRING_ANNOTATION,
)
from .conftest import CreateAppFileFixture

project_base = Path(__file__).parent.parent.parent


@pytest.fixture()
def mock_show_app_info(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("litestar.cli.commands.core.show_app_info")


@pytest.mark.parametrize("set_in_env", [True, False])
@pytest.mark.parametrize(
    "host, port, uds, fd",
    [("0.0.0.0", 8081, "/run/uvicorn/litestar_test.sock", 0), (None, None, None, None)],
)
@pytest.mark.parametrize("custom_app_file,", [Path("my_app.py"), None])
@pytest.mark.parametrize("app_dir", ["custom_subfolder", None])
@pytest.mark.parametrize(
    "reload, reload_dir, reload_include, reload_exclude, web_concurrency",
    [
        (None, None, None, None, None),
        (True, None, None, None, None),
        (False, None, None, None, None),
        (True, [".", "../somewhere_else"], None, None, None),
        (False, [".", "../somewhere_else"], None, None, None),
        (True, None, ["*.rst", "*.yml"], None, None),
        (False, None, None, ["*.py"], None),
        (False, None, ["*.yml", "*.rst"], None, None),
        (None, None, None, None, 2),
        (True, None, None, None, 2),
        (False, None, None, None, 2),
    ],
)
@pytest.mark.parametrize("tty_enabled", [True, False])
@pytest.mark.parametrize("quiet_console", [True, False])
def test_run_command(
    mock_show_app_info: MagicMock,
    mocker: MockerFixture,
    runner: CliRunner,
    monkeypatch: MonkeyPatch,
    reload: Optional[bool],
    port: Optional[int],
    host: Optional[str],
    fd: Optional[int],
    uds: Optional[str],
    web_concurrency: Optional[int],
    app_dir: Optional[str],
    reload_dir: Optional[List[str]],
    reload_include: Optional[List[str]],
    reload_exclude: Optional[List[str]],
    custom_app_file: Optional[Path],
    create_app_file: CreateAppFileFixture,
    set_in_env: bool,
    tty_enabled: bool,
    quiet_console: bool,
    mock_subprocess_run: MagicMock,
    mock_uvicorn_run: MagicMock,
    tmp_project_dir: Path,
) -> None:
    monkeypatch.delenv("LITESTAR_QUIET_CONSOLE", raising=False)
    if quiet_console:
        monkeypatch.setenv("LITESTAR_QUIET_CONSOLE", "true")
    mocker.patch.object(core, "isatty", return_value=tty_enabled)
    mocker.patch.object(_utils, "isatty", return_value=tty_enabled)
    args = []
    if custom_app_file:
        args.extend(["--app", f"{custom_app_file.stem}:app"])
    if app_dir is not None:
        args.extend(["--app-dir", str(Path(tmp_project_dir / app_dir))])
    args.extend(["run"])

    if reload:
        if set_in_env:
            monkeypatch.setenv("LITESTAR_RELOAD", "true")
        else:
            args.append("--reload")
    else:
        reload = False

    if port:
        if set_in_env:
            monkeypatch.setenv("LITESTAR_PORT", str(port))
        else:
            args.extend(["--port", str(port)])
    else:
        port = 8000

    if host:
        if set_in_env:
            monkeypatch.setenv("LITESTAR_HOST", host)
        else:
            args.extend(["--host", host])
    else:
        host = "127.0.0.1"

    if uds:
        if set_in_env:
            monkeypatch.setenv("LITESTAR_UNIX_DOMAIN_SOCKET", uds)
        else:
            args.extend(["--uds", uds])
    else:
        uds = None

    if fd is not None:
        if set_in_env:
            monkeypatch.setenv("LITESTAR_FILE_DESCRIPTOR", str(fd))
        else:
            args.extend(["--fd", str(fd)])
    else:
        fd = None

    if web_concurrency is None:
        web_concurrency = 1
    elif set_in_env:
        monkeypatch.setenv("LITESTAR_WEB_CONCURRENCY", str(web_concurrency))
    else:
        args.extend(["--web-concurrency", str(web_concurrency)])

    if reload_dir is not None:
        if set_in_env:
            monkeypatch.setenv("LITESTAR_RELOAD_DIRS", ",".join(reload_dir))
        else:
            args.extend([f"--reload-dir={s}" for s in reload_dir])

    if reload_include is not None:
        if set_in_env:
            monkeypatch.setenv("LITESTAR_RELOAD_INCLUDES", ",".join(reload_include))
        else:
            args.extend([f"--reload-include={s}" for s in reload_include])

    if reload_exclude is not None:
        if set_in_env:
            monkeypatch.setenv("LITESTAR_RELOAD_EXCLUDES", ",".join(reload_exclude))
        else:
            args.extend([f"--reload-exclude={s}" for s in reload_exclude])

    path = create_app_file(custom_app_file or "app.py", directory=app_dir)
    result = runner.invoke(cli_command, args)

    assert result.exception is None
    assert result.exit_code == 0

    if reload or reload_dir or reload_include or reload_exclude or web_concurrency > 1:
        expected_args = [
            sys.executable,
            "-m",
            "uvicorn",
            f"{path.stem}:app",
            f"--host={host}",
            f"--port={port}",
        ]
        if fd is not None:
            expected_args.append(f"--fd={fd}")
        if uds is not None:
            expected_args.append(f"--uds={uds}")
        if reload or reload_dir or reload_include or reload_exclude:
            expected_args.append("--reload")
        if web_concurrency:
            expected_args.append(f"--workers={web_concurrency}")
        if reload_dir:
            expected_args.extend([f"--reload-dir={s}" for s in reload_dir])
        if reload_include:
            expected_args.extend([f"--reload-include={s}" for s in reload_include])
        if reload_exclude:
            expected_args.extend([f"--reload-exclude={s}" for s in reload_exclude])
        mock_subprocess_run.assert_called_once()
        assert sorted(mock_subprocess_run.call_args_list[0].args[0]) == sorted(expected_args)
    else:
        mock_subprocess_run.assert_not_called()
        mock_uvicorn_run.assert_called_once_with(
            app=f"{path.stem}:app",
            host=host,
            port=port,
            uds=uds,
            fd=fd,
            factory=False,
            ssl_certfile=None,
            ssl_keyfile=None,
        )

    if tty_enabled and not quiet_console:
        mock_show_app_info.assert_called_once()
    else:
        mock_show_app_info.assert_not_called()


@pytest.mark.parametrize("quiet_console", [True, False])
@pytest.mark.parametrize("tty_enabled", [True, False])
@pytest.mark.parametrize(
    "file_name,file_content,factory_name",
    [
        ("_create_app.py", CREATE_APP_FILE_CONTENT, "create_app"),
        ("_generic_app_factory.py", GENERIC_APP_FACTORY_FILE_CONTENT, "any_name"),
        ("_generic_app_factory_string_ann.py", GENERIC_APP_FACTORY_FILE_CONTENT_STRING_ANNOTATION, "any_name"),
    ],
    ids=["create-app", "generic", "generic-string-annotated"],
)
def test_run_command_with_autodiscover_app_factory(
    runner: CliRunner,
    mock_uvicorn_run: MagicMock,
    file_name: str,
    file_content: str,
    factory_name: str,
    patch_autodiscovery_paths: Callable[[List[str]], None],
    tty_enabled: bool,
    quiet_console: bool,
    create_app_file: CreateAppFileFixture,
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("LITESTAR_QUIET_CONSOLE", raising=False)
    if quiet_console:
        monkeypatch.setenv("LITESTAR_QUIET_CONSOLE", "true")
    mocker.patch.object(core, "isatty", return_value=tty_enabled)
    mocker.patch.object(_utils, "isatty", return_value=tty_enabled)
    patch_autodiscovery_paths([file_name])
    path = create_app_file(file_name, content=file_content)
    result = runner.invoke(cli_command, "run")
    assert result.exception is None
    assert result.exit_code == 0

    mock_uvicorn_run.assert_called_once_with(
        app=f"{path.stem}:{factory_name}",
        host="127.0.0.1",
        port=8000,
        factory=True,
        uds=None,
        fd=None,
        ssl_certfile=None,
        ssl_keyfile=None,
    )
    if tty_enabled and not quiet_console:
        assert len(result.output) > 0
    else:
        assert len(result.output) == 0


@pytest.mark.parametrize("quiet_console", [True, False])
@pytest.mark.parametrize("tty_enabled", [True, False])
def test_run_command_with_app_factory(
    runner: CliRunner,
    mock_uvicorn_run: MagicMock,
    create_app_file: CreateAppFileFixture,
    tty_enabled: bool,
    quiet_console: bool,
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("LITESTAR_QUIET_CONSOLE", raising=False)
    if quiet_console:
        monkeypatch.setenv("LITESTAR_QUIET_CONSOLE", "true")
    mocker.patch.object(core, "isatty", return_value=tty_enabled)
    mocker.patch.object(_utils, "isatty", return_value=tty_enabled)
    path = create_app_file("_create_app_with_path.py", content=CREATE_APP_FILE_CONTENT)
    app_path = f"{path.stem}:create_app"
    result = runner.invoke(cli_command, ["--app", app_path, "run"])

    assert result.exception is None
    assert result.exit_code == 0

    mock_uvicorn_run.assert_called_once_with(
        app=str(app_path),
        host="127.0.0.1",
        port=8000,
        factory=True,
        uds=None,
        fd=None,
        ssl_certfile=None,
        ssl_keyfile=None,
    )
    if tty_enabled and not quiet_console:
        assert len(result.output) > 0
    else:
        assert len(result.output) == 0


@pytest.mark.parametrize(
    "cli, env, expected",
    (
        (
            ("--reload", True),
            ("LITESTAR_RELOAD", False),
            "--reload",
        ),
        (
            ("--reload-dir", [".", "../somewhere_else"]),
            ("LITESTAR_RELOAD_DIRS", ["../somewhere_else3", "../somewhere_else2"]),
            ["--reload-dir=.", "--reload-dir=../somewhere_else"],
        ),
        (
            ("--reload-include", ["*.rst", "*.yml"]),
            ("LITESTAR_RELOAD_INCLUDES", ["*.rst2", "*.yml2"]),
            ["--reload-include=*.rst", "--reload-include=*.yml"],
        ),
        (
            ("--reload-exclude", ["*.rst", "*.yml"]),
            ("LITESTAR_RELOAD_EXCLUDES", ["*.rst2", "*.yml2"]),
            ["--reload-exclude=*.rst", "--reload-exclude=*.yml"],
        ),
        (
            ("--wc", 2),
            ("LITESTAR_WEB_CONCURRENCY", 4),
            "--workers=2",
        ),
        (
            ("--fd", 0),
            ("LITESTAR_FILE_DESCRIPTOR", 1),
            "--fd=0",
        ),
        (
            ("--uds", "/run/uvicorn/litestar_test.sock"),
            ("LITESTAR_UNIX_DOMAIN_SOCKET", "/run/uvicorn/litestar_test2.sock"),
            "--uds=/run/uvicorn/litestar_test.sock",
        ),
        (
            ("-d", True),
            ("LITESTAR_DEBUG", False),
            ("LITESTAR_DEBUG", "1"),
        ),
        (
            ("--pdb", True),
            ("LITESTAR_PDB", False),
            ("LITESTAR_PDB", "1"),
        ),
    ),
)
def test_run_command_arguments_precedence(
    cli: Tuple[str, Union[Literal[True], List[str], str]],
    env: Tuple[str, Union[Literal[True], List[str], str]],
    expected: str,
    runner: CliRunner,
    monkeypatch: MonkeyPatch,
    mock_subprocess_run: MagicMock,
    tmp_project_dir: Path,
    create_app_file: CreateAppFileFixture,
    mock_uvicorn_run: MagicMock,
) -> None:
    args = []
    args.extend(["--app", f"{Path('my_app.py').stem}:app"])
    args.extend(["--app-dir", str(Path(tmp_project_dir / "custom_subfolder"))])
    args.extend(["run"])
    create_app_file("my_app.py", directory="custom_subfolder")

    env_name, env_value = env
    cli_name, cli_value = cli

    if env_name:
        if isinstance(env_value, list):
            monkeypatch.setenv(env_name, "".join(env_value))
        else:
            monkeypatch.setenv(env_name, env_value)  # type: ignore[arg-type] # pyright: ignore (reportGeneralTypeIssues)

    if cli_name:
        if cli_value is True:
            args.append(cli_name)
        elif isinstance(cli_value, list):
            for value in cli_value:
                args.extend([cli_name, value])
        else:
            args.extend([cli_name, cli_value])

    result = runner.invoke(cli_command, args)

    assert result.exception is None
    assert result.exit_code == 0

    if cli_name in ["--fd", "--uds"]:
        mock_subprocess_run.assert_not_called()
        if isinstance(expected, list):  # type: ignore[unreachable]
            assert all(_ in mock_uvicorn_run.call_args_list[0].args[0] for _ in expected)  # type: ignore[unreachable]
        else:
            assert mock_uvicorn_run.call_args_list[0].kwargs.get(cli_name.strip("--")) == cli_value

    elif cli_name in ["-d", "--pdb"]:
        assert os.environ.get(expected[0]) == expected[1]

    else:
        mock_subprocess_run.assert_called_once()

        if isinstance(expected, list):  # type: ignore[unreachable]
            assert all(_ in mock_subprocess_run.call_args_list[0].args[0] for _ in expected)  # type: ignore[unreachable]
        else:
            assert expected in mock_subprocess_run.call_args_list[0].args[0]


@pytest.fixture()
def unset_env() -> Generator[None, None, None]:
    initial_env = {**os.environ}
    yield
    for key in os.environ.keys() - initial_env.keys():
        del os.environ[key]

    os.environ.update(initial_env)


@pytest.mark.usefixtures("mock_uvicorn_run", "unset_env")
def test_run_command_debug(
    app_file: Path, runner: CliRunner, monkeypatch: MonkeyPatch, create_app_file: CreateAppFileFixture
) -> None:
    monkeypatch.delenv("LITESTAR_DEBUG", raising=False)
    path = create_app_file("_create_app_with_path.py", content=CREATE_APP_FILE_CONTENT)
    app_path = f"{path.stem}:create_app"
    result = runner.invoke(cli_command, ["--app", app_path, "run", "--debug"])

    assert result.exit_code == 0
    assert os.getenv("LITESTAR_DEBUG") == "1"


@pytest.mark.usefixtures("mock_uvicorn_run", "unset_env")
def test_run_command_quiet_console(
    app_file: Path,
    mocker: MockerFixture,
    runner: CliRunner,
    monkeypatch: MonkeyPatch,
    create_app_file: CreateAppFileFixture,
) -> None:
    mocker.patch.object(core, "isatty", return_value=True)
    mocker.patch.object(_utils, "isatty", return_value=True)
    console = Console(file=io.StringIO(), force_interactive=True)
    monkeypatch.setattr(_utils, "console", console)

    path = create_app_file("_create_app_with_path.py", content=CREATE_APP_FILE_CONTENT)
    app_path = f"{path.stem}:create_app"
    monkeypatch.delenv("LITESTAR_QUIET_CONSOLE", raising=False)
    result = runner.invoke(cli_command, ["--app", app_path, "run"])
    assert result.exit_code == 0
    normal_output = console.file.getvalue()  # type: ignore[attr-defined]
    assert "Using Litestar app from env:" in normal_output
    assert "Starting server process" in result.stdout
    del result
    console = Console(file=io.StringIO(), force_interactive=True)
    monkeypatch.setattr(_utils, "console", console)
    monkeypatch.setenv("LITESTAR_QUIET_CONSOLE", "1")
    assert os.getenv("LITESTAR_QUIET_CONSOLE") == "1"
    result = runner.invoke(cli_command, ["--app", app_path, "run"])
    assert result.exit_code == 0
    quiet_output = console.file.getvalue()  # type: ignore[attr-defined]
    assert "Starting server process" not in result.stdout
    assert "Using Litestar app from env:" not in quiet_output
    console.clear()


@pytest.mark.usefixtures("mock_uvicorn_run", "unset_env")
def test_run_command_custom_app_name(
    app_file: Path,
    runner: CliRunner,
    monkeypatch: MonkeyPatch,
    create_app_file: CreateAppFileFixture,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(core, "isatty", return_value=True)
    mocker.patch.object(_utils, "isatty", return_value=True)

    console = Console(file=io.StringIO(), force_interactive=True)
    monkeypatch.setattr(_utils, "console", console)

    path = create_app_file("_create_app_with_path.py", content=CREATE_APP_FILE_CONTENT)
    app_path = f"{path.stem}:create_app"
    monkeypatch.delenv("LITESTAR_APP_NAME", raising=False)
    result = runner.invoke(cli_command, ["--app", app_path, "run"])
    assert result.exit_code == 0
    _output = console.file.getvalue()  # type: ignore[attr-defined]
    assert "Using Litestar app from env:" in _output
    console = Console(file=io.StringIO(), force_interactive=True)
    monkeypatch.setattr(_utils, "console", console)
    monkeypatch.setenv("LITESTAR_APP_NAME", "My Stuff")
    assert os.getenv("LITESTAR_APP_NAME") == "My Stuff"
    result = runner.invoke(cli_command, ["--app", app_path, "run"])
    assert result.exit_code == 0
    _output = console.file.getvalue()  # type: ignore[attr-defined]
    assert "Using My Stuff app from env:" in _output


@pytest.mark.usefixtures("mock_uvicorn_run", "unset_env")
def test_run_command_pdb(
    app_file: Path,
    runner: CliRunner,
    monkeypatch: MonkeyPatch,
    create_app_file: CreateAppFileFixture,
) -> None:
    monkeypatch.delenv("LITESTAR_PDB", raising=False)
    path = create_app_file("_create_app_with_path.py", content=CREATE_APP_FILE_CONTENT)
    app_path = f"{path.stem}:create_app"

    with pytest.warns(LitestarWarning):
        result = runner.invoke(cli_command, ["--app", app_path, "run", "--pdb"])

    assert result.exit_code == 0
    assert os.getenv("LITESTAR_PDB") == "1"


@pytest.mark.usefixtures("mock_uvicorn_run", "unset_env")
def test_run_command_without_uvicorn_installed(
    app_file: Path,
    runner: CliRunner,
    monkeypatch: MonkeyPatch,
    create_app_file: CreateAppFileFixture,
    mocker: MockerFixture,
) -> None:
    mocker.patch("litestar.cli.commands.core.UVICORN_INSTALLED", False)
    console_print_mock = mocker.patch("litestar.cli.commands.core.console.print")
    path = create_app_file("_create_app_with_path.py", content=CREATE_APP_FILE_CONTENT)
    app_path = f"{path.stem}:create_app"

    result = runner.invoke(cli_command, ["--app", app_path, "run"])
    assert result.exit_code == 1
    assert any("uvicorn is not installed" in arg for args, kwargs in console_print_mock.call_args_list for arg in args)


@pytest.mark.parametrize("short", [True, False])
def test_version_command(short: bool, runner: CliRunner) -> None:
    result = runner.invoke(cli_command, "version --short" if short else "version")

    assert result.output.strip() == litestar_version.formatted(short=short)


@pytest.mark.usefixtures("mock_uvicorn_run", "unset_env")
def test_run_command_with_server_lifespan_plugin(
    runner: CliRunner, mock_uvicorn_run: MagicMock, create_app_file: CreateAppFileFixture
) -> None:
    path = create_app_file("_create_app_with_path.py", content=APP_FACTORY_FILE_CONTENT_SERVER_LIFESPAN_PLUGIN)
    app_path = f"{path.stem}:create_app"
    result = runner.invoke(cli_command, ["--app", app_path, "run"])

    assert result.exception is None
    assert result.exit_code == 0
    assert "i_run_before_startup_plugin" in result.stdout
    assert "i_run_after_shutdown_plugin" in result.stdout
    assert result.stdout.find("i_run_before_startup_plugin") < result.stdout.find("i_run_after_shutdown_plugin")

    mock_uvicorn_run.assert_called_once_with(
        app=str(app_path),
        host="127.0.0.1",
        port=8000,
        fd=None,
        uds=None,
        factory=True,
        ssl_certfile=None,
        ssl_keyfile=None,
    )


@pytest.mark.parametrize(
    "app_content, schema_enabled, exclude_pattern_list, expected_result_routes_count",
    [
        pytest.param(APP_FILE_CONTENT_ROUTES_EXAMPLE, False, (), 3, id="schema-disabled_no-exclude"),
        pytest.param(
            APP_FILE_CONTENT_ROUTES_EXAMPLE,
            False,
            ("/foo", "/destroy/.*", "/java", "/haskell"),
            2,
            id="schema-disabled_exclude",
        ),
        pytest.param(APP_FILE_CONTENT_ROUTES_EXAMPLE, True, (), 13, id="schema-enabled_no-exclude"),
        pytest.param(
            APP_FILE_CONTENT_ROUTES_EXAMPLE,
            True,
            ("/foo", "/destroy/.*", "/java", "/haskell"),
            12,
            id="schema-enabled_exclude",
        ),
    ],
)
@pytest.mark.xdist_group("cli_autodiscovery")
def test_routes_command_options(
    runner: CliRunner,
    app_content: str,
    schema_enabled: bool,
    exclude_pattern_list: Tuple[str, ...],
    create_app_file: CreateAppFileFixture,
    expected_result_routes_count: int,
) -> None:
    create_app_file("app.py", content=app_content)

    command = "routes"
    if schema_enabled:
        command += " --schema "
    if exclude_pattern_list:
        for pattern in exclude_pattern_list:
            command += f" --exclude={pattern}"

    result = runner.invoke(cli_command, command)
    assert result.exception is None
    assert result.exit_code == 0

    result_routes = [line for line in result.output.splitlines() if "(HTTP)" in line]
    for route in result_routes:
        root_dir = route.split(" ")[0]
        if not schema_enabled:
            assert root_dir != "/api-docs"

        assert root_dir not in exclude_pattern_list

    assert expected_result_routes_count == len(result_routes)


def test_remove_default_schema_routes() -> None:
    routes = [
        "/",
        "/schema",
        "/schema/elements",
        "/schema/oauth2-redirect.html",
        "/schema/openapi.json",
        "/schema/openapi.yaml",
        "/schema/openapi.yml",
        "/schema/rapidoc",
        "/schema/redoc",
        "/schema/swagger",
        "/destroy/all/foo/bar/schema",
        "/foo",
    ]
    http_routes = []
    for route in routes:
        http_route = MagicMock()
        http_route.path = route
        http_routes.append(http_route)

    api_config = MagicMock()
    api_config.openapi_controller.path = "/schema"

    results = _utils.remove_default_schema_routes(http_routes, api_config)  # type: ignore[arg-type]
    assert len(results) == 3
    for result in results:
        words = re.split(r"(^\/[a-z]+)", result.path)
        assert "/schema" not in words


def test_remove_routes_with_patterns() -> None:
    routes = ["/", "/destroy/all/foo/bar/schema", "/foo"]
    http_routes = []
    for route in routes:
        http_route = MagicMock()
        http_route.path = route
        http_routes.append(http_route)

    patterns = ("/destroy", "/pizza", "[]")
    results = _utils.remove_routes_with_patterns(http_routes, patterns)  # type: ignore[arg-type]
    paths = [route.path for route in results]
    assert len(paths) == 2
    for route in ["/", "/foo"]:
        assert route in paths
