from litestar.contrib.htmx.response import HTMXTemplate
from litestar.response import Template


@get(path="/form")
def get_form(
    request: HTMXRequest,
) -> Template:  # Return type is Template and not HTMXTemplate.
    return HTMXTemplate(
        template_name="partial.html",
        context=context,
        # Optional parameters
        push_url="/form",  # update browser history
        re_swap="outerHTML",  # change swapping method
        re_target="#new-target",  # change target element
        trigger_event="showMessage",  # trigger event name
        params={"alert": "Confirm your Choice."},  # parameter to pass to the event
        after="receive",  # when to trigger event,
        # possible values 'receive', 'settle', and 'swap'
    )
