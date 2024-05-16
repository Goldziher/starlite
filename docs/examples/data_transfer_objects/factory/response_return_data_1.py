from advanced_alchemy.dto import SQLAlchemyDTO

from litestar.dto import DTOConfig


class UserDTO(SQLAlchemyDTO[User]):
    config = DTOConfig(exclude={"password", "created_at"})
