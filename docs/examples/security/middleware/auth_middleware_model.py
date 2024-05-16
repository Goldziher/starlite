import uuid

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    id: uuid.UUID | None = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    # ... other fields follow, but we only require id for this example
