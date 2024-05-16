subscriber = await channels.subscribe(["foo", "bar"])
try:
    ...  # do some stuff here
finally:
    await channels.unsubscribe(subscriber)
