from jinja2 import DictLoader, Environment

from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template import TemplateConfig

my_custom_env = Environment(loader=DictLoader({"index.html": "Hello {{name}}!"}))
app = Litestar(template_config=TemplateConfig(instance=JinjaTemplateEngine.from_environment(my_custom_env)))
