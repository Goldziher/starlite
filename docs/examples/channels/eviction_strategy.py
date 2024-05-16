from litestar.channels import ChannelsPlugin
from litestar.channels.memory import MemoryChannelsBackend

channels = ChannelsPlugin(
    backend=MemoryChannelsBackend(),
    max_backlog=1000,
    backlog_strategy="dropleft",
)
