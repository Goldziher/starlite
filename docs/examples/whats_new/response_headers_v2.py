from litestar import ResponseHeader, get


@get(response_headers=[ResponseHeader(name="my-header", value="header-value")])
async def handler() -> str: ...


# or


@get(response_headers={"my-header": "header-value"})
async def handler() -> str: ...
