import secrets
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from litestar.testing import TestClient


@pytest.fixture(autouse=True)
def _chdir(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


@pytest.fixture()
def assets_file(tmp_path: Path) -> str:
    content = secrets.token_hex()
    assets_path = tmp_path / "assets"
    assets_path.mkdir()
    assets_path.joinpath("test.txt").write_text(content)
    return content


def test_custom_router() -> None:
    from docs.examples.static_files import custom_router  # noqa: F401


def test_full_example() -> None:
    from docs.examples.static_files import full_example

    with TestClient(full_example.app) as client:
        assert client.get("/static/hello.txt").text == "Hello, world!"


def test_html_mode() -> None:
    from docs.examples.static_files import html_mode

    with TestClient(html_mode.app) as client:
        assert client.get("/").text == "<strong>Hello, world!</strong>"
        assert client.get("/index.html").text == "<strong>Hello, world!</strong>"
        assert client.get("/something").text == "<h1>Not found</h1>"


def test_passing_options() -> None:
    from docs.examples.static_files import passing_options  # noqa: F401


def test_route_reverse(capsys) -> None:
    from docs.examples.static_files import route_reverse  # noqa: F401

    assert capsys.readouterr().out.strip() == "/static/some_file.txt"


def test_send_as_attachment(tmp_path: Path, assets_file: str) -> None:
    from docs.examples.static_files import send_as_attachment

    with TestClient(send_as_attachment.app) as client:
        res = client.get("/static/test.txt")
        assert res.text == assets_file
        assert res.headers["content-disposition"].startswith("attachment")


def test_upgrade_from_static(tmp_path: Path, assets_file: str) -> None:
    from docs.examples.static_files import upgrade_from_static_1, upgrade_from_static_2

    for app in [upgrade_from_static_1.app, upgrade_from_static_2.app]:
        with TestClient(app) as client:
            res = client.get("/static/test.txt")
            assert res.text == assets_file
