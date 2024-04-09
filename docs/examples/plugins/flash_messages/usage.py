from litestar import Litestar, Request, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.plugins.flash import FlashConfig, FlashPlugin, flash
from litestar.response import Template
from litestar.template.config import TemplateConfig

template_config = TemplateConfig(engine=JinjaTemplateEngine, directory="templates")
flash_plugin = FlashPlugin(config=FlashConfig(template_config=template_config))


@get()
async def index(request: Request) -> Template:
    """Example of adding and displaying a flash message."""
    flash(request, "Oh no! I've been flashed!", category="error")

    return Template(
        template_str="""
    <h1>Flash Message Example</h1>
    {% for message in get_flashes() %}
    <p>{{ message.message }} (Category:{{ message.category }})</p>
    {% endfor %}
    """
    )


app = Litestar(plugins=[flash_plugin], route_handlers=[index], template_config=template_config)
