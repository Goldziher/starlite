@get("/")
def handler() -> HXStopPolling:
    return HXStopPolling()
