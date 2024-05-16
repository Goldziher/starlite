from enum import Enum

from pydantic import UUID4, BaseModel

from litestar import post
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler


class UserRole(str, Enum):
    CONSUMER = "consumer"
    ADMIN = "admin"


class User(BaseModel):
    id: UUID4
    role: UserRole

    @property
    def is_admin(self) -> bool:
        """Determines whether the user is an admin user"""
        return self.role == UserRole.ADMIN


def admin_user_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.user.is_admin:
        raise NotAuthorizedException()


@post(path="/user", guards=[admin_user_guard])
def create_user(data: User) -> User: ...
