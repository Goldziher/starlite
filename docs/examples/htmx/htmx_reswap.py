@get("/contact-us")
def handler() -> Reswap:
    return Reswap(content="Success!", method="beforebegin")
