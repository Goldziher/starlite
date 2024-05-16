@get()
async def example() -> Template:
    template_string = "{{ hello }}"
    return Template(template_str=template_string, context={"hello": "world"})
