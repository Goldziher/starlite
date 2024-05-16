from starlite import ResponseHeader, get


@get(response_headers={"my-header": ResponseHeader(value="header-value")})
async def handler() -> str: ...
