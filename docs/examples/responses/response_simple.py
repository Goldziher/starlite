from pydantic import BaseModel

from litestar import get


class Resource(BaseModel):
    id: int
    name: str


@get("/resources")
def retrieve_resource() -> Resource:
    return Resource(id=1, name="my resource")
