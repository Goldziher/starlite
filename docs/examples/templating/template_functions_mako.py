from pathlib import Path
from typing import Dict

from litestar import Litestar, get
from litestar.contrib.mako import MakoTemplateEngine
from litestar.response_containers import Template
from litestar.template.config import TemplateConfig


def my_template_function(ctx: Dict) -> str:
    return ctx.get("my_context_key", "nope")


def register_template_callables(engine: MakoTemplateEngine) -> None:
    engine.register_template_callable(
        key="check_context_key",
        template_callable=my_template_function,
    )


template_config = TemplateConfig(
    directory=Path("templates"),
    engine=MakoTemplateEngine,
    engine_callback=register_template_callables,
)


@get("/")
def index() -> Template:
    return Template(name="index.html.mako")


app = Litestar(
    route_handlers=[index],
    template_config=template_config,
)
