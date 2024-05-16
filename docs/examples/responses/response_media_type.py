from litestar import MediaType, get


@get("/resources", media_type=MediaType.TEXT)
def retrieve_resource() -> str:
    return "The rumbling rabbit ran around the rock"
