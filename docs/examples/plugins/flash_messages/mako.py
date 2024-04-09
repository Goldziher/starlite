from litestar import Litestar
from litestar.contrib.mako import MakoTemplateEngine
from litestar.plugins.flash import FlashConfig, FlashPlugin
from litestar.template.config import TemplateConfig

template_config = TemplateConfig(engine=MakoTemplateEngine, directory="templates")
flash_plugin = FlashPlugin(config=FlashConfig(template_config=template_config))

app = Litestar(plugins=[flash_plugin])
