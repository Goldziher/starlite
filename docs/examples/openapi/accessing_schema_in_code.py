from litestar import Request, get


@get(path="/")
def my_route_handler(request: Request) -> dict:
    schema = request.app.openapi_schema
    return schema.dict()
