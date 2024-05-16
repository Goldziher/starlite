from litestar import Litestar, get
from litestar.exceptions import HTTPException


@get("/")
def index() -> None:
    raise HTTPException(status_code=400, detail="this did not work")


app = Litestar([index])
