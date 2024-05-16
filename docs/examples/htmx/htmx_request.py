from pathlib import Path

from litestar import Litestar, get
from litestar.contrib.htmx.request import HTMXRequest
from litestar.contrib.htmx.response import HTMXTemplate
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.template.config import TemplateConfig


@get(path="/form")
def get_form(request: HTMXRequest) -> Template:
    htmx = request.htmx  # if true will return HTMXDetails class object
    if htmx:
        print(htmx.current_url)
    # OR
    if request.htmx:
        print(request.htmx.current_url)
    return HTMXTemplate(template_name="partial.html", context=context, push_url="/form")


app = Litestar(
    route_handlers=[get_form],
    debug=True,
    request_class=HTMXRequest,
    template_config=TemplateConfig(
        directory=Path("litestar_htmx/templates"),
        engine=JinjaTemplateEngine,
    ),
)
