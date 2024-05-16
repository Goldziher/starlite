@get("/about")
def handler() -> HXLocation:
    return HXLocation(
        redirect_to="/contact-us",
        # Optional parameters
        source=source,  # the source element of the request.
        event=event,  # an event that "triggered" the request.
        target="#target",  # element id to target to.
        swap="outerHTML",  # swapping method to use.
        hx_headers={"attr": "val"},  # headers to pass to htmx.
        values={"val": "one"},
    )  # values to submit with response.
