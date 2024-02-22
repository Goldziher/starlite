from __future__ import annotations

from pathlib import Path

from click import Context, group, option, pass_context
from click import Path as ClickPath

from ._utils import LitestarEnv, LitestarExtensionGroup
from .commands import core, schema, sessions

__all__ = ("litestar_group",)


@group(cls=LitestarExtensionGroup, context_settings={"help_option_names": ["-h", "--help"]})
@option("--app", "app_path", help="Module path to a Litestar application")
@option(
    "--app-dir",
    help="Look for APP in the specified directory, by adding this to the PYTHONPATH. Defaults to the current working directory.",
    default=None,
    type=ClickPath(dir_okay=True, file_okay=False, path_type=Path),
    show_default=False,
)
@pass_context
def litestar_group(ctx: Context, app_path: str | None, app_dir: Path | None = None) -> None:
    """Litestar CLI."""
    if ctx.obj is None:  # env has not been loaded yet, so we can lazy load it
        ctx.obj = lambda: LitestarEnv.from_env(app_path, app_dir=app_dir)


# add sub commands here

litestar_group.add_command(core.info_command)
litestar_group.add_command(core.run_command)
litestar_group.add_command(core.routes_command)
litestar_group.add_command(core.version_command)
litestar_group.add_command(sessions.sessions_group)
litestar_group.add_command(schema.schema_group)
