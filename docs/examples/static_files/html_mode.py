from pathlib import Path

from litestar import Litestar
from litestar.static_files import create_static_files_router

HTML_DIR = Path("html")


def on_startup() -> None:
    HTML_DIR.mkdir(exist_ok=True)
    HTML_DIR.joinpath("index.html").write_text("<strong>Hello, world!</strong>")
    HTML_DIR.joinpath("404.html").write_text("<h1>Not found</h1>")


app = Litestar(
    route_handlers=[
        create_static_files_router(
            path="/",
            directories=["html"],
            html_mode=True,
        )
    ],
    on_startup=[on_startup],
)


# run: /
# run: /index.html
# run: /something
