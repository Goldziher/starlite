from __future__ import annotations

import gzip
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import brotli
import pytest
from typing_extensions import TypeAlias

from litestar import MediaType, Router, get
from litestar.static_files import StaticFilesConfig, create_static_files_router
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client
from tests.unit.test_static_files.conftest import MakeConfig

if TYPE_CHECKING:
    from litestar.types import FileSystemProtocol


def test_default_static_files_config(tmpdir: Path, make_config: MakeConfig) -> None:
    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")
    static_files_config, router = make_config(StaticFilesConfig(path="/static", directories=[tmpdir]))

    with create_test_client(router, static_files_config=static_files_config) as client:
        response = client.get("/static/test.txt")
        assert response.status_code == HTTP_200_OK, response.text
        assert response.text == "content"


@pytest.fixture()
def setup_dirs(tmpdir: Path) -> tuple[Path, Path]:
    paths = []
    for i in range(1, 3):
        root = tmpdir / str(i)
        root.mkdir()
        file_path = root / f"test_{i}.txt"
        file_path.write_text(f"content{i}", "utf-8")
        paths.append(root)

    return paths[0], paths[1]


MakeConfigs: TypeAlias = (
    "Callable[[StaticFilesConfig, StaticFilesConfig], tuple[list[StaticFilesConfig], list[Router]]]"
)


@pytest.fixture()
def make_configs(make_config: MakeConfig) -> MakeConfigs:
    def make(
        first_config: StaticFilesConfig, second_config: StaticFilesConfig
    ) -> tuple[list[StaticFilesConfig], list[Router]]:
        configs_1, routers_1 = make_config(first_config)
        configs_2, routers_2 = make_config(second_config)
        return [*configs_1, *configs_2], [*routers_1, *routers_2]

    return make


def test_multiple_static_files_configs(setup_dirs: tuple[Path, Path], make_configs: MakeConfigs) -> None:
    root1, root2 = setup_dirs

    configs, handlers = make_configs(
        StaticFilesConfig(path="/static_first", directories=[root1]),  # pyright: ignore
        StaticFilesConfig(path="/static_second", directories=[root2]),  # pyright: ignore
    )
    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/static_first/test_1.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content1"

        response = client.get("/static_second/test_2.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content2"


def test_static_files_configs_with_mixed_file_systems(
    file_system: FileSystemProtocol, setup_dirs: tuple[Path, Path], make_configs: MakeConfigs
) -> None:
    root1, root2 = setup_dirs

    configs, handlers = make_configs(
        StaticFilesConfig(path="/static_first", directories=[root1], file_system=file_system),  # pyright: ignore
        StaticFilesConfig(path="/static_second", directories=[root2]),  # pyright: ignore
    )

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/static_first/test_1.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content1"

        response = client.get("/static_second/test_2.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content2"


def test_static_files_config_with_multiple_directories(
    file_system: FileSystemProtocol, setup_dirs: tuple[Path, Path], make_config: MakeConfig
) -> None:
    root1, root2 = setup_dirs
    configs, handlers = make_config(
        StaticFilesConfig(path="/static", directories=[root1, root2], file_system=file_system)
    )

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/static/test_1.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content1"

        response = client.get("/static/test_2.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content2"


def test_staticfiles_for_slash_path_regular_mode(tmpdir: Path, make_config: MakeConfig) -> None:
    path = tmpdir / "text.txt"
    path.write_text("content", "utf-8")

    configs, handlers = make_config(StaticFilesConfig(path="/", directories=[tmpdir]))

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/text.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"


def test_staticfiles_for_slash_path_html_mode(tmpdir: Path, make_config: MakeConfig) -> None:
    path = tmpdir / "index.html"
    path.write_text("<html></html>", "utf-8")

    configs, handlers = make_config(StaticFilesConfig(path="/", directories=[tmpdir], html_mode=True))

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "<html></html>"


def test_sub_path_under_static_path(tmpdir: Path, make_config: MakeConfig) -> None:
    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    @get("/static/sub/{f:str}", media_type=MediaType.TEXT)
    def handler(f: str) -> str:
        return f

    configs, handlers = make_config(StaticFilesConfig(path="/static", directories=[tmpdir]))
    handlers.append(handler)  # type: ignore[arg-type]

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/static/test.txt")
        assert response.status_code == HTTP_200_OK

        response = client.get("/static/sub/abc")
        assert response.status_code == HTTP_200_OK


def test_static_substring_of_self(tmpdir: Path, make_config: MakeConfig) -> None:
    path = tmpdir.mkdir("static_part").mkdir("static") / "test.txt"  # type: ignore
    path.write_text("content", "utf-8")

    configs, handlers = make_config(StaticFilesConfig(path="/static", directories=[tmpdir]))
    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/static/static_part/static/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"


@pytest.mark.parametrize("extension", ["css", "js", "html", "json"])
def test_static_files_response_mimetype(tmpdir: Path, extension: str, make_config: MakeConfig) -> None:
    fn = f"test.{extension}"
    path = tmpdir / fn
    path.write_text("content", "utf-8")
    configs, handlers = make_config(StaticFilesConfig(path="/static", directories=[tmpdir]))
    expected_mime_type = mimetypes.guess_type(fn)[0]

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get(f"/static/{fn}")
        assert expected_mime_type
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"].startswith(expected_mime_type)


@pytest.mark.parametrize("extension", ["gz", "br"])
def test_static_files_response_encoding(tmp_path: Path, extension: str, make_config: MakeConfig) -> None:
    fn = f"test.js.{extension}"
    path = tmp_path / fn
    compressed_data = None
    if extension == "br":
        compressed_data = brotli.compress(b"content")
    elif extension == "gz":
        compressed_data = gzip.compress(b"content")
    path.write_bytes(compressed_data)  # type: ignore[arg-type]
    expected_encoding_type = mimetypes.guess_type(fn)[1]

    configs, handlers = make_config(StaticFilesConfig(path="/static", directories=[tmp_path]))

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get(f"/static/{fn}")
        assert expected_encoding_type
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-encoding"].startswith(expected_encoding_type)


@pytest.mark.parametrize("send_as_attachment,disposition", [(True, "attachment"), (False, "inline")])
def test_static_files_content_disposition(
    tmpdir: Path, send_as_attachment: bool, disposition: str, make_config: MakeConfig
) -> None:
    path = tmpdir.mkdir("static_part").mkdir("static") / "test.txt"  # type: ignore
    path.write_text("content", "utf-8")

    configs, handlers = make_config(
        StaticFilesConfig(path="/static", directories=[tmpdir], send_as_attachment=send_as_attachment)
    )

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/static/static_part/static/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-disposition"].startswith(disposition)


def test_service_from_relative_path_using_string(tmpdir: Path, make_config: MakeConfig) -> None:
    sub_dir = Path(tmpdir.mkdir("low")).resolve()  # type: ignore

    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    configs, handlers = make_config(StaticFilesConfig(path="/static", directories=[f"{sub_dir}/.."]))

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/static/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"


def test_service_from_relative_path_using_path(tmpdir: Path, make_config: MakeConfig) -> None:
    sub_dir = Path(tmpdir.mkdir("low")).resolve()  # type: ignore

    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    configs, handlers = make_config(StaticFilesConfig(path="/static", directories=[Path(f"{sub_dir}/..")]))

    with create_test_client(handlers, static_files_config=configs) as client:
        response = client.get("/static/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"


def test_service_from_base_path_using_string(tmpdir: Path) -> None:
    sub_dir = Path(tmpdir.mkdir("low")).resolve()  # type: ignore

    path = tmpdir / "test.txt"
    path.write_text("content", "utf-8")

    @get("/", media_type=MediaType.TEXT)
    def index_handler() -> str:
        return "index"

    @get("/sub")
    def sub_handler() -> dict:
        return {"hello": "world"}

    static_files_config = StaticFilesConfig(path="/", directories=[f"{sub_dir}/.."])
    with create_test_client([index_handler, sub_handler], static_files_config=[static_files_config]) as client:
        response = client.get("/test.txt")
        assert response.status_code == HTTP_200_OK
        assert response.text == "content"

        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.text == "index"

        response = client.get("/sub")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"hello": "world"}


@pytest.mark.parametrize("resolve", [True, False])
def test_resolve_symlinks(tmp_path: Path, resolve: bool) -> None:
    source_dir = tmp_path / "foo"
    source_dir.mkdir()
    linked_dir = tmp_path / "bar"
    linked_dir.symlink_to(source_dir, target_is_directory=True)
    source_dir.joinpath("test.txt").write_text("hello")

    router = create_static_files_router(path="/", directories=[linked_dir], resolve_symlinks=resolve)

    with create_test_client(router) as client:
        if not resolve:
            linked_dir.unlink()
            assert client.get("/test.txt").status_code == 404
        else:
            assert client.get("/test.txt").status_code == 200
