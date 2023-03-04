from __future__ import annotations

from click import Context, group, option, pass_context

from .commands import core, schema, sessions
from .utils import StarliteEnv, StarliteExtensionGroup

__all__ = ("starlite_group",)


@group(cls=StarliteExtensionGroup)
@option("--app", "app_path", help="Module path to a Starlite application")
@pass_context
def starlite_group(ctx: Context, app_path: str | None) -> None:
    """Starlite CLI."""

    ctx.obj = StarliteEnv.from_env(app_path)


# add sub commands here

starlite_group.add_command(core.info_command)
starlite_group.add_command(core.run_command)
starlite_group.add_command(core.routes_command)
starlite_group.add_command(sessions.sessions_group)
starlite_group.add_command(schema.schema_group)
