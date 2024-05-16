from litestar import Litestar, Request, Response
from litestar.exceptions import HTTPException


def handle_exception(request: Request, exception: Exception) -> Response: ...


app = Litestar([], exception_handlers={HTTPException: handle_exception})
