from litestar import Litestar, get
from litestar.response import Redirect


@get("/")
def index() -> str:
    return "hello"


@get("/hello")
def hello() -> Redirect:
    return Redirect(path="index")


app = Litestar([index, hello])
