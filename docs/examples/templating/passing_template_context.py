from litestar import get
from litestar.response import Template


@get(path="/info")
def info() -> Template:
    return Template(template_name="info.html", context={"numbers": "1234567890"})
