import sys
from pathlib import Path
from typing import Optional, Protocol, cast
from unittest.mock import MagicMock

import pytest
from click import ClickException
from click.testing import CliRunner
from pytest_mock import MockerFixture

from litestar.cli.main import litestar_group as cli_command


class GetClickExceptionFixture(Protocol):
    def __call__(self, exception: SystemExit) -> ClickException: ...


@pytest.fixture
def get_click_exception() -> GetClickExceptionFixture:
    def _get_click_exception(exception: SystemExit) -> ClickException:
        exc = exception
        while exc.__context__ is not None:
            if isinstance(exc, ClickException):
                break
            exc = exc.__context__  # type: ignore[assignment]
        return cast(ClickException, exc)

    return _get_click_exception


@pytest.mark.parametrize("create_self_signed_cert", (True, False))
@pytest.mark.usefixtures("mock_uvicorn_run")
def test_both_files_provided(app_file: Path, runner: CliRunner, create_self_signed_cert: bool) -> None:
    path = app_file
    app_path = f"{path.stem}:app"

    cert_path = path.parent / "cert.pem"
    with cert_path.open("wb") as certfile:
        certfile.write(b"certfile")

    key_path = path.parent / "key.pem"
    with key_path.open("wb") as keyfile:
        keyfile.write(b"keyfile")

    args = ["--app", app_path, "run", "--ssl-certfile", str(cert_path), "--ssl-keyfile", str(key_path)]

    if create_self_signed_cert:
        args.append("--create-self-signed-cert")

    result = runner.invoke(cli_command, args)

    assert result.exception is None
    assert result.exit_code == 0

    if create_self_signed_cert:
        with cert_path.open("rb") as certfile:
            assert certfile.read() == b"certfile"

        with key_path.open("rb") as keyfile:
            assert keyfile.read() == b"keyfile"


@pytest.mark.parametrize("create_self_signed_cert", (True, False))
@pytest.mark.parametrize(
    "ssl_certfile, ssl_keyfile",
    [("directory", "exists.pem"), ("exists.pem", "directory")],
)
def test_path_is_a_directory(
    app_file: Path,
    runner: CliRunner,
    ssl_certfile: str,
    ssl_keyfile: str,
    create_self_signed_cert: bool,
    get_click_exception: GetClickExceptionFixture,
) -> None:
    path = app_file
    app_path = f"{path.stem}:app"

    (path.parent / "exists.pem").touch()
    (path.parent / "directory").mkdir(exist_ok=True)

    args = ["--app", app_path, "run", "--ssl-certfile", ssl_certfile, "--ssl-keyfile", ssl_keyfile]

    if create_self_signed_cert:
        args.append("--create-self-signed-cert")

    result = runner.invoke(cli_command, args)

    assert result.exit_code == 1

    assert isinstance(result.exception, SystemExit)
    exc = get_click_exception(result.exception)
    assert "Path provided for" in exc.message
    assert "is a directory" in exc.message


@pytest.mark.parametrize("create_self_signed_cert", (True, False))
@pytest.mark.parametrize(
    "ssl_certfile, ssl_keyfile",
    [("exists.pem", None), (None, "exists.pem")],
)
def test_one_file_provided(
    app_file: Path,
    runner: CliRunner,
    ssl_certfile: Optional[str],
    ssl_keyfile: Optional[str],
    create_self_signed_cert: bool,
    get_click_exception: GetClickExceptionFixture,
) -> None:
    path = app_file
    app_path = f"{path.stem}:app"

    (path.parent / "exists.pem").touch()

    args = ["--app", app_path, "run"]

    if ssl_certfile is not None:
        args.extend(["--ssl-certfile", str(ssl_certfile)])

    if ssl_keyfile is not None:
        args.extend(["--ssl-keyfile", str(ssl_keyfile)])

    if create_self_signed_cert:
        args.append("--create-self-signed-cert")

    result = runner.invoke(cli_command, args)

    assert result.exit_code == 1

    assert isinstance(result.exception, SystemExit)
    exc = get_click_exception(result.exception)
    assert "No value provided for" in exc.message


@pytest.mark.parametrize("create_self_signed_cert", (True, False))
@pytest.mark.parametrize(
    "ssl_certfile, ssl_keyfile",
    [("not_exists.pem", "exists.pem"), ("exists.pem", "not_exists.pem")],
)
def test_one_file_not_found(
    app_file: Path,
    runner: CliRunner,
    ssl_certfile: str,
    ssl_keyfile: str,
    create_self_signed_cert: bool,
    get_click_exception: GetClickExceptionFixture,
) -> None:
    path = app_file
    app_path = f"{path.stem}:app"

    (path.parent / "exists.pem").touch()

    args = ["--app", app_path, "run"]

    if ssl_certfile is not None:
        args.extend(["--ssl-certfile", ssl_certfile])

    if ssl_keyfile is not None:
        args.extend(["--ssl-keyfile", ssl_keyfile])

    if create_self_signed_cert:
        args.append("--create-self-signed-cert")

    result = runner.invoke(cli_command, args)

    assert result.exit_code == 1

    assert isinstance(result.exception, SystemExit)
    exc = get_click_exception(result.exception)
    if create_self_signed_cert:
        assert (
            "Both certificate and key file must exists or both must not exists when using --create-self-signed-cert"
            in exc.message
        )
    else:
        assert "File provided for" in exc.message
        assert "was not found" in exc.message


@pytest.mark.parametrize(
    "ssl_certfile, ssl_keyfile",
    [("dir_exists/file.pem", "dir_not_exists/file.pem"), ("dir_not_exists/file.pem", "dir_exists/file.pem")],
)
def test_file_parent_doesnt_exist(
    app_file: Path,
    runner: CliRunner,
    ssl_certfile: str,
    ssl_keyfile: str,
    get_click_exception: GetClickExceptionFixture,
) -> None:
    path = app_file
    app_path = f"{path.stem}:app"

    (path.parent / "dir_exists").mkdir(exist_ok=True)

    args = [
        "--app",
        app_path,
        "run",
        "--ssl-certfile",
        ssl_certfile,
        "--ssl-keyfile",
        ssl_keyfile,
        "--create-self-signed-cert",
    ]

    result = runner.invoke(cli_command, args)

    assert result.exit_code == 1

    assert isinstance(result.exception, SystemExit)
    exc = get_click_exception(result.exception)
    assert "Could not create file, parent directory for" in exc.message
    assert "doesn't exist" in exc.message


def test_without_cryptography_installed(
    app_file: Path,
    runner: CliRunner,
    get_click_exception: GetClickExceptionFixture,
    mocker: MockerFixture,
) -> None:
    mocker.patch.dict("sys.modules", {"cryptography": None})

    path = app_file
    app_path = f"{path.stem}:app"

    args = [
        "--app",
        app_path,
        "run",
        "--ssl-certfile",
        "certfile.pem",
        "--ssl-keyfile",
        "keyfile.pem",
        "--create-self-signed-cert",
    ]

    result = runner.invoke(cli_command, args)

    assert result.exit_code == 1

    assert isinstance(result.exception, SystemExit)
    exc = get_click_exception(result.exception)
    assert "Cryptography must be installed when using --create-self-signed-cert" in exc.message


@pytest.mark.usefixtures("mock_uvicorn_run")
def test_create_certificates(app_file: Path, runner: CliRunner) -> None:
    path = app_file
    app_path = f"{path.stem}:app"

    certfile_path = path.parent / "certificate.pem"
    keyfile_path = path.parent / "key.pem"

    args = [
        "--app",
        app_path,
        "run",
        "--ssl-certfile",
        str(certfile_path),
        "--ssl-keyfile",
        str(keyfile_path),
        "--create-self-signed-cert",
    ]

    result = runner.invoke(cli_command, args)

    assert result.exit_code == 0
    assert result.exception is None

    assert certfile_path.exists()
    assert keyfile_path.exists()


@pytest.mark.parametrize(
    "ssl_certfile, ssl_keyfile, create_self_signed_cert", [(None, None, False), ("cert.pem", "key.pem", True)]
)
@pytest.mark.parametrize("run_as_subprocess", (True, False))
def test_arguments_passed(
    app_file: Path,
    runner: CliRunner,
    mock_subprocess_run: MagicMock,
    mock_uvicorn_run: MagicMock,
    ssl_certfile: Optional[str],
    ssl_keyfile: Optional[str],
    create_self_signed_cert: bool,
    run_as_subprocess: bool,
) -> None:
    path = app_file
    app_path = f"{path.stem}:app"

    project_path = path.parent

    args = ["--app", app_path, "run"]

    if run_as_subprocess:
        args.extend(["--web-concurrency", "2"])

    if ssl_certfile is not None:
        args.extend(["--ssl-certfile", str(ssl_certfile)])

    if ssl_keyfile is not None:
        args.extend(["--ssl-keyfile", str(ssl_keyfile)])

    if create_self_signed_cert:
        args.append("--create-self-signed-cert")

    result = runner.invoke(cli_command, args)

    assert result.exit_code == 0
    assert result.exception is None

    if run_as_subprocess:
        expected_args = [
            sys.executable,
            "-m",
            "uvicorn",
            f"{path.stem}:app",
            "--host=127.0.0.1",
            "--port=8000",
            "--workers=2",
        ]
        if ssl_certfile is not None:
            expected_args.append(f"--ssl-certfile={project_path / ssl_certfile}")
        if ssl_keyfile is not None:
            expected_args.append(f"--ssl-keyfile={project_path / ssl_keyfile}")

        mock_subprocess_run.assert_called_once()
        assert sorted(mock_subprocess_run.call_args_list[0].args[0]) == sorted(expected_args)

    else:
        mock_subprocess_run.assert_not_called()
        mock_uvicorn_run.assert_called_once_with(
            app=f"{path.stem}:app",
            host="127.0.0.1",
            port=8000,
            factory=False,
            fd=None,
            uds=None,
            ssl_certfile=(None if ssl_certfile is None else str(project_path / ssl_certfile)),
            ssl_keyfile=(None if ssl_keyfile is None else str(project_path / ssl_keyfile)),
        )
