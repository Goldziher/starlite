"""Litestar CLI."""

from __future__ import annotations

from importlib.util import find_spec

# Ensure `rich_click` patching occurs before we do any imports from `click`.
if find_spec("rich_click") is not None:  # pragma: no cover
    import rich_click as click
    from rich_click.cli import patch as rich_click_patch

    rich_click_patch()
    click.rich_click.USE_RICH_MARKUP = True
    click.rich_click.USE_MARKDOWN = False
    click.rich_click.SHOW_ARGUMENTS = True
    click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
    click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
    click.rich_click.ERRORS_SUGGESTION = ""
    click.rich_click.ERRORS_EPILOGUE = ""
    click.rich_click.MAX_WIDTH = 80
    click.rich_click.SHOW_METAVARS_COLUMN = True
    click.rich_click.APPEND_METAVARS_HELP = True


from .main import litestar_group

__all__ = ["litestar_group"]
