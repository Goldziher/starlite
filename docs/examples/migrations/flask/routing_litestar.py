from litestar import Litestar, get


@get("/")
def index() -> str:
    return "Index Page"


@get("/hello")
def hello() -> str:
    return "Hello, World"


app = Litestar([index, hello])
