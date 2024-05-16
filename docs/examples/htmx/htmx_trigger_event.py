@get("/contact-us")
def handler() -> TriggerEvent:
    return TriggerEvent(
        content="Success!",
        name="showMessage",
        params={"attr": "value"},
        after="receive",  # possible values 'receive', 'settle', and 'swap'
    )
