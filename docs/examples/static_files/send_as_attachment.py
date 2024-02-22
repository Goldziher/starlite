from litestar import Litestar
from litestar.static_files import create_static_files_router

app = Litestar(
    route_handlers=[
        create_static_files_router(
            path="/static",
            directories=["assets"],
            send_as_attachment=True,
        )
    ]
)
