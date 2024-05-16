from litestar import Litestar, MediaType, get


@get("/json")
def get_json() -> dict[str, str]:
    return {"hello": "world"}


@get("/text", media_type=MediaType.TEXT)
def get_text() -> str:
    return "hello, world"


@get("/html", media_type=MediaType.HTML)
def get_html() -> str:
    return "<strong>hello, world</strong>"


app = Litestar([get_json, get_text, get_html])
