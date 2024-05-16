@get("/")
def handler() -> ClientRefresh:
    return ClientRefresh()
