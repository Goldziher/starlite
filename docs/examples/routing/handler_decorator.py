from pydantic import BaseModel

from litestar import delete, get, head, patch, post, put
from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig, DTOData


class Resource(BaseModel): ...


class PartialResourceDTO(PydanticDTO[Resource]):
    config = DTOConfig(partial=True)


@get(path="/resources")
async def list_resources() -> list[Resource]: ...


@post(path="/resources")
async def create_resource(data: Resource) -> Resource: ...


@get(path="/resources/{pk:int}")
async def retrieve_resource(pk: int) -> Resource: ...


@head(path="/resources/{pk:int}")
async def retrieve_resource_head(pk: int) -> None: ...


@put(path="/resources/{pk:int}")
async def update_resource(data: Resource, pk: int) -> Resource: ...


@patch(path="/resources/{pk:int}", dto=PartialResourceDTO)
async def partially_update_resource(data: DTOData[PartialResourceDTO], pk: int) -> Resource: ...


@delete(path="/resources/{pk:int}")
async def delete_resource(pk: int) -> None: ...
