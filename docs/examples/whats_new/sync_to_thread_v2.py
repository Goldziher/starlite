@get(sync_to_thread=False)
def handler() -> None: ...


# or


@get(sync_to_thread=True)
def handler() -> None: ...
