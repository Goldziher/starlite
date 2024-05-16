async with channels.start_subscription(["foo", "bar"]) as subscriber:
    # do some stuff here
    await channels.unsubscribe(subscriber, ["foo"])
