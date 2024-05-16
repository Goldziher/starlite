from pydantic import UUID4, BaseModel


class User(BaseModel):
    first_name: str
    last_name: str
    id: UUID4
