from litestar import Litestar, WebSocket, websocket
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend


@websocket("/ws")
async def handler(socket: WebSocket, channels: ChannelsPlugin) -> None:
    await socket.accept()

    async with channels.start_subscription(["some_channel"]) as subscriber:
        async for message in subscriber.iter_events():
            await socket.send_text(message)


app = Litestar(
    [handler],
    plugins=[ChannelsPlugin(backend=MemoryChannelsBackend())],
)
