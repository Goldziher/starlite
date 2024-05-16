from litestar import get


@get("/", opt={"my_key": "some-value"})
def handler() -> None: ...
