from litestar import Litestar, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.template.config import TemplateConfig


@get("/hello/{name:str}")
def hello(name: str) -> Template:
    return Template(response_name="hello.html", context={"name": name})


app = Litestar(
    [hello],
    template_config=TemplateConfig(directory="templates", engine=JinjaTemplateEngine),
)
