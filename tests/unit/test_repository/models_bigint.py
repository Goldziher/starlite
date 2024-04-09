"""Example domain objects for testing."""

from __future__ import annotations

from datetime import date, datetime
from typing import List

from advanced_alchemy import SQLAlchemyAsyncRepository, SQLAlchemySyncRepository
from advanced_alchemy.base import BigIntAuditBase, BigIntBase
from sqlalchemy import Column, FetchedValue, ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class BigIntAuthor(BigIntAuditBase):
    """The Author domain object."""

    name: Mapped[str] = mapped_column(String(length=100))  # pyright: ignore
    dob: Mapped[date] = mapped_column(nullable=True)  # pyright: ignore
    books: Mapped[List[BigIntBook]] = relationship(  # noqa
        lazy="selectin",
        back_populates="author",
        cascade="all, delete",
    )


class BigIntBook(BigIntBase):
    """The Book domain object."""

    title: Mapped[str] = mapped_column(String(length=250))  # pyright: ignore
    author_id: Mapped[int] = mapped_column(ForeignKey("big_int_author.id"))  # pyright: ignore
    author: Mapped[BigIntAuthor] = relationship(  # pyright: ignore
        lazy="joined",
        innerjoin=True,
        back_populates="books",
    )


class BigIntEventLog(BigIntAuditBase):
    """The event log domain object."""

    logged_at: Mapped[datetime] = mapped_column(default=datetime.now())  # pyright: ignore
    payload: Mapped[dict] = mapped_column(default=lambda: {})  # pyright: ignore


class BigIntModelWithFetchedValue(BigIntBase):
    """The ModelWithFetchedValue BigIntBase."""

    val: Mapped[int]  # pyright: ignore
    updated: Mapped[datetime] = mapped_column(  # pyright: ignore
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        server_onupdate=FetchedValue(),
    )


bigint_item_tag = Table(
    "bigint_item_tag",
    BigIntBase.metadata,
    Column("item_id", ForeignKey("big_int_item.id"), primary_key=True),
    Column("tag_id", ForeignKey("big_int_tag.id"), primary_key=True),
)


class BigIntItem(BigIntBase):
    name: Mapped[str] = mapped_column(String(length=50))  # pyright: ignore
    description: Mapped[str] = mapped_column(String(length=100), nullable=True)  # pyright: ignore
    tags: Mapped[List[BigIntTag]] = relationship(secondary=lambda: bigint_item_tag, back_populates="items")  # noqa


class BigIntTag(BigIntBase):
    """The event log domain object."""

    name: Mapped[str] = mapped_column(String(length=50))  # pyright: ignore
    items: Mapped[List[BigIntItem]] = relationship(secondary=lambda: bigint_item_tag, back_populates="tags")  # noqa


class BigIntRule(BigIntAuditBase):
    """The rule domain object."""

    name: Mapped[str] = mapped_column(String(length=250))  # pyright: ignore
    config: Mapped[dict] = mapped_column(default=lambda: {})  # pyright: ignore


class RuleAsyncRepository(SQLAlchemyAsyncRepository[BigIntRule]):
    """Rule repository."""

    model_type = BigIntRule


class AuthorAsyncRepository(SQLAlchemyAsyncRepository[BigIntAuthor]):
    """Author repository."""

    model_type = BigIntAuthor


class BookAsyncRepository(SQLAlchemyAsyncRepository[BigIntBook]):
    """Book repository."""

    model_type = BigIntBook


class EventLogAsyncRepository(SQLAlchemyAsyncRepository[BigIntEventLog]):
    """Event log repository."""

    model_type = BigIntEventLog


class ModelWithFetchedValueAsyncRepository(SQLAlchemyAsyncRepository[BigIntModelWithFetchedValue]):
    """BigIntModelWithFetchedValue repository."""

    model_type = BigIntModelWithFetchedValue


class TagAsyncRepository(SQLAlchemyAsyncRepository[BigIntTag]):
    """Tag repository."""

    model_type = BigIntTag


class ItemAsyncRepository(SQLAlchemyAsyncRepository[BigIntItem]):
    """Item repository."""

    model_type = BigIntItem


class AuthorSyncRepository(SQLAlchemySyncRepository[BigIntAuthor]):
    """Author repository."""

    model_type = BigIntAuthor


class BookSyncRepository(SQLAlchemySyncRepository[BigIntBook]):
    """Book repository."""

    model_type = BigIntBook


class EventLogSyncRepository(SQLAlchemySyncRepository[BigIntEventLog]):
    """Event log repository."""

    model_type = BigIntEventLog


class RuleSyncRepository(SQLAlchemySyncRepository[BigIntRule]):
    """Rule repository."""

    model_type = BigIntRule


class ModelWithFetchedValueSyncRepository(SQLAlchemySyncRepository[BigIntModelWithFetchedValue]):
    """ModelWithFetchedValue repository."""

    model_type = BigIntModelWithFetchedValue


class TagSyncRepository(SQLAlchemySyncRepository[BigIntTag]):
    """Tag repository."""

    model_type = BigIntTag


class ItemSyncRepository(SQLAlchemySyncRepository[BigIntItem]):
    """Item repository."""

    model_type = BigIntItem
