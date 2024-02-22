from litestar import Litestar
from litestar.static_files import create_static_files_router

app = Litestar(
    route_handlers=[
        create_static_files_router(path="/static", directories=["assets"]),
    ]
)


print(app.route_reverse(name="static", file_path="/some_file.txt"))  # /static/some_file.txt
