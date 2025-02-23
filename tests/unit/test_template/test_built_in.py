from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import pytest
from jinja2 import DictLoader, Environment
from mako.lookup import TemplateLookup  # type: ignore[import-untyped]

from litestar import get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.contrib.mako import MakoTemplateEngine
from litestar.contrib.minijinja import MiniJinjaTemplateEngine
from litestar.response.template import Template
from litestar.template.config import TemplateConfig
from litestar.testing import create_test_client

if TYPE_CHECKING:
    from litestar.handlers.http_handlers import HTTPRouteHandler


@dataclass
class EngineTest:
    engine_class: Optional[type[Union[JinjaTemplateEngine, MakoTemplateEngine, MiniJinjaTemplateEngine]]]
    index_template: str
    nested_template: str
    instantiated: bool
    instance: Optional[Union[JinjaTemplateEngine, MakoTemplateEngine, MiniJinjaTemplateEngine]]


mako_template_lookup = TemplateLookup()
mako_template_lookup.put_string("index.html", "<html>Injected? ${test}</html>")
mako_template_lookup.put_string("nested-dir/nested.html", "<html>Does nested dirs work? ${test}</html>")
mako_template_lookup.put_string("no_context.html", "<html>This works!</html>")


@pytest.fixture(
    params=[
        EngineTest(
            engine_class=JinjaTemplateEngine,
            index_template="<html>Injected? {{test}}</html>",
            nested_template="<html>Does nested dirs work? {{test}}</html>",
            instantiated=False,
            instance=None,
        ),
        EngineTest(
            engine_class=MakoTemplateEngine,
            index_template="<html>Injected? ${test}</html>",
            nested_template="<html>Does nested dirs work? ${test}</html>",
            instantiated=False,
            instance=None,
        ),
        EngineTest(
            engine_class=MiniJinjaTemplateEngine,
            index_template="<html>Injected? {{test}}</html>",
            nested_template="<html>Does nested dirs work? {{test}}</html>",
            instantiated=False,
            instance=None,
        ),
        EngineTest(
            engine_class=None,
            index_template="<html>Injected? {{test}}</html>",
            nested_template="<html>Does nested dirs work? {{test}}</html>",
            instantiated=True,
            instance=JinjaTemplateEngine.from_environment(
                Environment(
                    loader=DictLoader(
                        {
                            "index.html": "<html>Injected? {{test}}</html>",
                            "nested-dir/nested.html": "<html>Does nested dirs work? {{test}}</html>",
                            "no_context.html": "<html>This works!</html>",
                        }
                    )
                )
            ),
        ),
        EngineTest(
            engine_class=None,
            index_template="<html>Injected? ${test}</html>",
            nested_template="<html>Does nested dirs work? ${test}</html>",
            instantiated=True,
            instance=MakoTemplateEngine.from_template_lookup(mako_template_lookup),
        ),
    ]
)
def engine_test(request: Any) -> EngineTest:
    return request.param  # type:ignore[no-any-return]


@pytest.fixture()
def index_handler(engine_test: EngineTest, tmp_path: Path) -> "HTTPRouteHandler":
    Path(tmp_path / "index.html").write_text(engine_test.index_template)

    @get(path="/")
    def index_handler() -> Template:
        return Template(template_name="index.html", context={"test": "yep"})

    return index_handler


@pytest.fixture()
def nested_path_handler(engine_test: EngineTest, tmp_path: Path) -> "HTTPRouteHandler":
    nested_path = tmp_path / "nested-dir"
    nested_path.mkdir()
    Path(nested_path / "nested.html").write_text(engine_test.nested_template)

    @get(path="/nested")
    def nested_path_handler() -> Template:
        return Template(template_name="nested-dir/nested.html", context={"test": "yep"})

    return nested_path_handler


@pytest.fixture()
def template_config(engine_test: EngineTest, tmp_path: Path) -> TemplateConfig:
    if engine_test.instantiated:
        return TemplateConfig(instance=engine_test.instance)
    return TemplateConfig(engine=engine_test.engine_class, directory=tmp_path)


def test_template(index_handler: "HTTPRouteHandler", template_config: TemplateConfig) -> None:
    with create_test_client(route_handlers=[index_handler], template_config=template_config) as client:
        response = client.request("GET", "/")
        assert response.status_code == 200, response.text
        assert response.text == "<html>Injected? yep</html>"
        assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_nested_tmp_pathectory(nested_path_handler: "HTTPRouteHandler", template_config: TemplateConfig) -> None:
    with create_test_client(route_handlers=[nested_path_handler], template_config=template_config) as client:
        response = client.request("GET", "/nested")
        assert response.status_code == 200, response.text
        assert response.text == "<html>Does nested dirs work? yep</html>"
        assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_raise_for_invalid_template_name(template_config: TemplateConfig) -> None:
    @get(path="/")
    def invalid_template_name_handler() -> Template:
        return Template(template_name="invalid.html", context={"test": "yep"})

    with create_test_client(
        route_handlers=[invalid_template_name_handler], template_config=template_config, debug=False
    ) as client:
        response = client.request("GET", "/")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal Server Error", "status_code": 500}


def test_no_context(tmp_path: Path, template_config: TemplateConfig) -> None:
    Path(tmp_path / "no_context.html").write_text("<html>This works!</html>")

    @get(path="/")
    def index() -> Template:
        return Template(template_name="no_context.html")

    with create_test_client(route_handlers=[index], template_config=template_config) as client:
        index_response = client.request("GET", "/")
        assert index_response.status_code == 200
        assert index_response.text == "<html>This works!</html>"
        assert index_response.headers["Content-Type"] == "text/html; charset=utf-8"
