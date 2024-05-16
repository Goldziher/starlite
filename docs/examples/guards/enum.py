from enum import Enum


class UserRole(str, Enum):
    CONSUMER = "consumer"
    ADMIN = "admin"
