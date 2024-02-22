from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from litestar import Litestar, MediaType, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.contrib.mako import MakoTemplateEngine
from litestar.contrib.minijinja import MiniJinjaTemplateEngine
from litestar.exceptions import ImproperlyConfiguredException
from litestar.response.template import Template
from litestar.template import TemplateEngineProtocol
from litestar.template.config import TemplateConfig
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from litestar import Request


def test_handler_raise_for_no_template_engine() -> None:
    @get(path="/")
    def invalid_path() -> Template:
        return Template(template_name="index.html", context={"ye": "yeeee"})

    with create_test_client(route_handlers=[invalid_path], debug=False) as client:
        response = client.request("GET", "/")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal Server Error", "status_code": 500}


def test_engine_passed_to_callback(tmp_path: Path) -> None:
    received_engine: JinjaTemplateEngine | None = None

    def callback(engine: TemplateEngineProtocol) -> None:
        nonlocal received_engine
        assert isinstance(engine, JinjaTemplateEngine), "Engine must be a JinjaTemplateEngine"
        received_engine = engine

    app = Litestar(
        route_handlers=[],
        template_config=TemplateConfig(
            directory=tmp_path,
            engine=JinjaTemplateEngine,
            engine_callback=callback,
        ),
    )

    assert received_engine is not None
    assert received_engine is app.template_engine


@pytest.mark.parametrize("engine", (JinjaTemplateEngine, MakoTemplateEngine, MiniJinjaTemplateEngine))
def test_engine_instance(engine: type[TemplateEngineProtocol], tmp_path: Path) -> None:
    engine_instance = engine(directory=tmp_path, engine_instance=None)
    if isinstance(engine_instance, JinjaTemplateEngine):
        assert engine_instance.engine.autoescape is True

    if isinstance(engine_instance, MakoTemplateEngine):
        assert engine_instance.engine.template_args["default_filters"] == ["h"]

    config = TemplateConfig(engine=engine_instance)
    assert config.engine_instance is engine_instance


@pytest.mark.parametrize("engine", (JinjaTemplateEngine, MakoTemplateEngine, MiniJinjaTemplateEngine))
def test_directory_validation(engine: type[TemplateEngineProtocol], tmp_path: Path) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        TemplateConfig(engine=engine)


@pytest.mark.parametrize("engine", (JinjaTemplateEngine, MakoTemplateEngine, MiniJinjaTemplateEngine))
def test_instance_and_directory_validation(engine: type[TemplateEngineProtocol], tmp_path: Path) -> None:
    with pytest.raises(ImproperlyConfiguredException):
        TemplateConfig(engine=engine, instance=engine(directory=tmp_path, engine_instance=None))


@pytest.mark.parametrize("media_type", [MediaType.HTML, MediaType.TEXT, "text/arbitrary"])
def test_media_type(media_type: MediaType | str, tmp_path: Path) -> None:
    (tmp_path / "hello.tpl").write_text("hello")

    @get("/", media_type=media_type)
    def index() -> Template:
        return Template(template_name="hello.tpl")

    with create_test_client(
        [index], template_config=TemplateConfig(directory=tmp_path, engine=JinjaTemplateEngine)
    ) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith(
            media_type if isinstance(media_type, str) else media_type.value,  # type: ignore[union-attr]
        )


@pytest.mark.parametrize(
    "extension,expected_type",
    [
        (".json", MediaType.JSON.value),
        (".html", MediaType.HTML.value),
        (".html.other", MediaType.HTML.value),
        (".css", MediaType.CSS.value),
        (".xml", MediaType.XML.value),
        (".xml.other", MediaType.XML.value),
        (".txt", MediaType.TEXT.value),
        (".unknown", MediaType.TEXT.value),
        ("", MediaType.TEXT.value),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", reason="mimetypes.guess_types is unreliable on windows")
def test_media_type_inferred(extension: str, expected_type: MediaType, tmp_path: Path) -> None:
    tpl_name = f"hello{extension}"
    (tmp_path / tpl_name).write_text("hello")

    @get("/")
    def index() -> Template:
        return Template(template_name=tpl_name)

    with create_test_client(
        [index], template_config=TemplateConfig(directory=tmp_path, engine=JinjaTemplateEngine)
    ) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith(expected_type)


def test_before_request_handler_content_type(tmp_path: Path) -> None:
    template_loc = tmp_path / "about.html"

    def before_request_handler(_: Request) -> None:
        template_loc.write_text("before request")

    @get("/", before_request=before_request_handler)
    def index() -> Template:
        return Template(template_name="about.html")

    with create_test_client(
        [index], template_config=TemplateConfig(directory=tmp_path, engine=JinjaTemplateEngine)
    ) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith(MediaType.HTML.value)
        assert res.text == "before request"


test_cases = [
    {"name": "both", "template_name": "dummy.html", "template_str": "Dummy", "raises": ValueError},
    {"name": "none", "template_name": None, "template_str": None, "status_code": 500},
    {"name": "name_only", "template_name": "dummy.html", "template_str": None, "status_code": 200},
    {"name": "str_only", "template_name": None, "template_str": "Dummy", "status_code": 200},
]


@pytest.mark.parametrize("engine", (JinjaTemplateEngine, MakoTemplateEngine, MiniJinjaTemplateEngine))
@pytest.mark.parametrize("test_case", test_cases, ids=[case["name"] for case in test_cases])  # type: ignore[index]
def test_template_scenarios(tmp_path: Path, engine: TemplateEngineProtocol, test_case: dict) -> None:
    if test_case["template_name"]:
        template_loc = tmp_path / test_case["template_name"]
        template_loc.write_text("Test content for template")

    @get("/")
    def index() -> Template:
        return Template(template_name=test_case["template_name"], template_str=test_case["template_str"])

    with create_test_client([index], template_config=TemplateConfig(directory=tmp_path, engine=engine)) as client:
        if "raises" in test_case and test_case["raises"] is ValueError:
            response = client.get("/")
            assert response.status_code == 500
            assert "ValueError" in response.text

        else:
            response = client.get("/")
            assert response.status_code == test_case["status_code"]

            if test_case["status_code"] == 200:
                if test_case["template_str"]:
                    assert response.text == test_case["template_str"]
                else:
                    assert response.text == "Test content for template"

            elif test_case["status_code"] == 500:
                assert "Either template_name or template_str must be provided" in response.text
