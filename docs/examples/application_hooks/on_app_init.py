from typing import TYPE_CHECKING

from starlite import Starlite

if TYPE_CHECKING:
    from starlite.config import AppConfig


async def close_db_connection() -> None:
    """Closes the database connection on application shutdown."""


def receive_app_config(app_config: "AppConfig") -> "AppConfig":
    """Receives parameters from the application.

    In reality, this would be a library of boilerplate that is carried from one application to another, or a third-party
    developed application configuration tool.
    """
    app_config.on_shutdown.append(close_db_connection)
    return app_config


app = Starlite([], on_app_init=[receive_app_config])
