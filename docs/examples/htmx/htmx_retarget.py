@get("/contact-us")
def handler() -> Retarget:
    return Retarget(content="Success!", target="#new-target")
