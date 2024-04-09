from litestar import Litestar, WebSocket, websocket
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend


@websocket("/ws")
async def handler(socket: WebSocket, channels: ChannelsPlugin) -> None:
    await socket.accept()

    async with channels.start_subscription(["some_channel"]) as subscriber:
        await channels.put_subscriber_history(subscriber, ["some_channel"], limit=10)


app = Litestar(
    [handler],
    plugins=[ChannelsPlugin(backend=MemoryChannelsBackend(history=20))],
)
