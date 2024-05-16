from pydantic import BaseModel

from litestar import get
from litestar.status_codes import HTTP_202_ACCEPTED


class Resource(BaseModel):
    id: int
    name: str


@get("/resources", status_code=HTTP_202_ACCEPTED)
def retrieve_resource() -> Resource:
    return Resource(id=1, name="my resource")
