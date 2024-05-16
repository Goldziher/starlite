from click import Group

from litestar import Litestar
from litestar.plugins import CLIPluginProtocol


class CLIPlugin(CLIPluginProtocol):
    def on_cli_init(self, cli: Group) -> None:
        @cli.command()
        def is_debug_mode(app: Litestar):
            print(app.debug)


app = Litestar(plugins=[CLIPlugin()])
