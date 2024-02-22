from pathlib import Path

from litestar import Litestar
from litestar.static_files import create_static_files_router

ASSETS_DIR = Path("assets")


def on_startup():
    ASSETS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.joinpath("hello.txt").write_text("Hello, world!")


app = Litestar(
    route_handlers=[
        create_static_files_router(path="/static", directories=["assets"]),
    ],
    on_startup=[on_startup],
)


#  run: /static/hello.txt
