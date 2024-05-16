from litestar import get


@get("/", my_key="some-value")
def handler() -> None: ...


assert handler.opt["my_key"] == "some-value"
