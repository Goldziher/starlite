import click

from litestar import Litestar


@click.command()
def my_command(app: Litestar) -> None: ...
