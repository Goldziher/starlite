from pathlib import Path

from starlite import Starlite
from starlite.middleware.session.server_side import ServerSideSessionConfig
from starlite.storage.file import FileStorage

storage = FileStorage(path=Path(".sessions"))
session_config = ServerSideSessionConfig(storage=storage)


async def clear_expired_sessions() -> None:
    """Delete all expired sessions."""
    await storage.delete_expired()


app = Starlite(
    middleware=[session_config.middleware],
    on_startup=[clear_expired_sessions],
    on_shutdown=[clear_expired_sessions],
)
