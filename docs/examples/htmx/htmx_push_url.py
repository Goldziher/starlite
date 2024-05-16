@get("/about")
def handler() -> PushUrl:
    return PushUrl(content="Success!", push_url="/about")
