@get("/")
def handler() -> ClientRedirect:
    return ClientRedirect(redirect_to="/contact-us")
