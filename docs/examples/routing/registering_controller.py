from pydantic import UUID4, BaseModel

from litestar.contrib.pydantic import PydanticDTO
from litestar.controller import Controller
from litestar.dto import DTOConfig, DTOData
from litestar.handlers import delete, get, patch, post


class UserOrder(BaseModel):
    user_id: int
    order: str


class PartialUserOrderDTO(PydanticDTO[UserOrder]):
    config = DTOConfig(partial=True)


class UserOrderController(Controller):
    path = "/user-order"

    @post()
    async def create_user_order(self, data: UserOrder) -> UserOrder: ...

    @get(path="/{order_id:uuid}")
    async def retrieve_user_order(self, order_id: UUID4) -> UserOrder: ...

    @patch(path="/{order_id:uuid}", dto=PartialUserOrderDTO)
    async def update_user_order(self, order_id: UUID4, data: DTOData[PartialUserOrderDTO]) -> UserOrder: ...

    @delete(path="/{order_id:uuid}")
    async def delete_user_order(self, order_id: UUID4) -> None: ...
