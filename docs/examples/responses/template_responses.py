from litestar import Request, get
from litestar.response import Template


@get(path="/info")
def info(request: Request) -> Template:
    return Template(template_name="info.html", context={"user": request.user})
