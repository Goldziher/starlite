@get("/contact-us")
def handler() -> ReplaceUrl:
    return ReplaceUrl(content="Success!", replace_url="/contact-us")
