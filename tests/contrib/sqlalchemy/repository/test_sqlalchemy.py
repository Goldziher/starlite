"""Unit tests for the SQLAlchemy Repository implementation."""
from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, call
from uuid import UUID

import pytest
from sqlalchemy import NullPool, insert
from sqlalchemy.exc import IntegrityError, InvalidRequestError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from starlite.contrib.repository.exceptions import ConflictError, RepositoryError
from starlite.contrib.repository.filters import (
    BeforeAfter,
    CollectionFilter,
    LimitOffset,
)
from starlite.contrib.sqlalchemy import base
from starlite.contrib.sqlalchemy.repository import (
    SQLAlchemyRepository,
    wrap_sqlalchemy_exception,
)
from tests.contrib.sqlalchemy.models import Author, AuthorRepository, BookRepository

if TYPE_CHECKING:
    from pytest import MonkeyPatch


@pytest.fixture()
def mock_repo() -> SQLAlchemyRepository:
    """SQLAlchemy repository with a mock model type."""

    class Repo(SQLAlchemyRepository[MagicMock]):
        """Repo with mocked out stuff."""

        model_type = MagicMock()  # pyright:ignore[reportGeneralTypeIssues]

    return Repo(session=AsyncMock(spec=AsyncSession), base_select=MagicMock())


async def test_sqlalchemy_tablename(monkeypatch: MonkeyPatch) -> None:
    """Test the snake case conversion for table names."""

    class BigModel(base.AuditBase):
        """Inheriting from AuditBase gives the model 'created' and 'updated'
        columns."""

        ...

    class TESTModel(base.AuditBase):
        """Inheriting from AuditBase gives the model 'created' and 'updated'
        columns."""

        ...

    assert BigModel.__tablename__ == "big_model"
    assert TESTModel.__tablename__ == "test_model"


def test_wrap_sqlalchemy_integrity_error() -> None:
    """Test to ensure we wrap IntegrityError."""
    with pytest.raises(ConflictError), wrap_sqlalchemy_exception():
        raise IntegrityError(None, None, Exception())


def test_wrap_sqlalchemy_generic_error() -> None:
    """Test to ensure we wrap generic SQLAlchemy exceptions."""
    with pytest.raises(RepositoryError), wrap_sqlalchemy_exception():
        raise SQLAlchemyError


async def test_sqlalchemy_repo_add(mock_repo: SQLAlchemyRepository) -> None:
    """Test expected method calls for add operation."""
    mock_instance = MagicMock()
    instance = await mock_repo.add(mock_instance)
    assert instance is mock_instance
    mock_repo.session.add.assert_called_once_with(mock_instance)
    mock_repo.session.flush.assert_called_once()
    mock_repo.session.refresh.assert_called_once_with(mock_instance)
    mock_repo.session.expunge.assert_called_once_with(mock_instance)
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_add_many(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test expected method calls for add many operation."""

    class Model(base.AuditBase):
        """Inheriting from AuditBase gives the model 'created' and 'updated'
        columns."""

        ...

    mock_instances = [MagicMock(), MagicMock(), MagicMock()]

    monkeypatch.setattr(mock_repo, "model_type", Model)
    monkeypatch.setattr(mock_repo, "_execute", AsyncMock(return_value=mock_instances))

    instances = await mock_repo.add_many(mock_instances)

    #
    assert instances is mock_instances
    mock_repo.session.expunge.assert_called()
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_update_many(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test expected method calls for update many operation."""

    class Model(base.AuditBase):
        """Inheriting from AuditBase gives the model 'created' and 'updated'
        columns."""

        ...

    mock_instances = [MagicMock(), MagicMock(), MagicMock()]

    monkeypatch.setattr(mock_repo, "model_type", Model)
    monkeypatch.setattr(mock_repo, "_execute", AsyncMock(return_value=mock_instances))

    instances = await mock_repo.update_many(mock_instances)

    assert instances is mock_instances
    mock_repo.session.flush.assert_called_once()
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_delete(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test expected method calls for delete operation."""
    mock_instance = MagicMock()
    monkeypatch.setattr(mock_repo, "get", AsyncMock(return_value=mock_instance))
    instance = await mock_repo.delete("instance-id")
    assert instance is mock_instance
    mock_repo.session.delete.assert_called_once_with(mock_instance)
    mock_repo.session.flush.assert_called_once()
    mock_repo.session.expunge.assert_called_once_with(mock_instance)
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_get_member(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test expected method calls for member get operation."""
    mock_instance = MagicMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_instance)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instance = await mock_repo.get("instance-id")
    assert instance is mock_instance
    mock_repo.session.expunge.assert_called_once_with(mock_instance)
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_get_one_member(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test expected method calls for member get one operation."""
    mock_instance = MagicMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_instance)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instance = await mock_repo.get_one(id="instance-id")
    assert instance is mock_instance
    mock_repo.session.expunge.assert_called_once_with(mock_instance)
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_get_or_create_member_existing(
    mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch
) -> None:
    """Test expected method calls for member get or create operation (existing)."""
    mock_instance = MagicMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_instance)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instance, created = await mock_repo.get_or_create(id="instance-id")
    assert instance is mock_instance
    assert created is False
    mock_repo.session.expunge.assert_called_once_with(mock_instance)
    mock_repo.session.add.assert_not_called()


async def test_sqlalchemy_repo_get_or_create_member_created(
    mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch
) -> None:
    """Test expected method calls for member get or create operation (created)."""
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instance, created = await mock_repo.get_or_create(id="new-id")
    assert instance is not None
    assert created is True
    mock_repo.session.expunge.assert_called_once_with(instance)
    mock_repo.session.add.assert_called_once_with(instance)


async def test_sqlalchemy_repo_get_one_or_none_member(
    mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch
) -> None:
    """Test expected method calls for member get one or none operation (found)."""
    mock_instance = MagicMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_instance)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instance = await mock_repo.get_one_or_none(id="instance-id")
    assert instance is mock_instance
    mock_repo.session.expunge.assert_called_once_with(mock_instance)
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_get_one_or_none_not_found(
    mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch
) -> None:
    """Test expected method calls for member get one or none operation (Not found)."""

    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instance = await mock_repo.get_one_or_none(id="instance-id")
    assert instance is None
    mock_repo.session.expunge.assert_not_called()
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_list(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test expected method calls for list operation."""
    mock_instances = [MagicMock(), MagicMock()]
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=mock_instances)
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instances = await mock_repo.list()
    assert instances == mock_instances
    mock_repo.session.expunge.assert_has_calls(*mock_instances)
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_list_and_count(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test expected method calls for list operation."""
    mock_instances = [MagicMock(), MagicMock()]
    mock_count = len(mock_instances)
    result_mock = MagicMock()
    result_mock.__iter__.return_value = iter([(mock, mock_count) for mock in mock_instances])
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    instances, instance_count = await mock_repo.list_and_count()
    assert instances == mock_instances
    assert instance_count == mock_count
    mock_repo.session.expunge.assert_has_calls(*mock_instances)
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_count(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test expected method calls for list operation."""
    result_mock = MagicMock()
    count_mock = MagicMock()
    execute_mock = AsyncMock(return_value=result_mock)
    execute_count_mock = AsyncMock(return_value=count_mock)
    monkeypatch.setattr(mock_repo, "count", execute_count_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    mock_repo.count.return_value = 1
    count = await mock_repo.count()
    assert count == 1
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_list_with_pagination(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test list operation with pagination."""
    result_mock = MagicMock()
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    mock_repo.select.limit.return_value = mock_repo.select
    mock_repo.select.offset.return_value = mock_repo.select
    await mock_repo.list(LimitOffset(2, 3))
    mock_repo.select.limit.assert_called_once_with(2)
    mock_repo.select.limit().offset.assert_called_once_with(3)  # type:ignore[call-arg]


async def test_sqlalchemy_repo_list_with_before_after_filter(
    mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch
) -> None:
    """Test list operation with BeforeAfter filter."""
    field_name = "updated"
    # model has to support comparison with the datetimes
    getattr(mock_repo.model_type, field_name).__lt__ = lambda self, compare: "lt"
    getattr(mock_repo.model_type, field_name).__gt__ = lambda self, compare: "gt"
    result_mock = MagicMock()
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    mock_repo.select.where.return_value = mock_repo.select
    await mock_repo.list(BeforeAfter(field_name, datetime.max, datetime.min))
    assert mock_repo.select.where.call_count == 2
    assert mock_repo.select.where.has_calls([call("gt"), call("lt")])


async def test_sqlalchemy_repo_list_with_collection_filter(
    mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch
) -> None:
    """Test behavior of list operation given CollectionFilter."""
    field_name = "id"
    result_mock = MagicMock()
    execute_mock = AsyncMock(return_value=result_mock)
    monkeypatch.setattr(mock_repo, "_execute", execute_mock)
    mock_repo.select.where.return_value = mock_repo.select
    values = [1, 2, 3]
    await mock_repo.list(CollectionFilter(field_name, values))
    mock_repo.select.where.assert_called_once()
    getattr(mock_repo.model_type, field_name).in_.assert_called_once_with(values)


async def test_sqlalchemy_repo_unknown_filter_type_raises(mock_repo: SQLAlchemyRepository) -> None:
    """Test that repo raises exception if list receives unknown filter type."""
    with pytest.raises(RepositoryError):
        await mock_repo.list("not a filter")  # type:ignore[arg-type]


async def test_sqlalchemy_repo_update(mock_repo: SQLAlchemyRepository, monkeypatch: MonkeyPatch) -> None:
    """Test the sequence of repo calls for update operation."""
    id_ = 3
    mock_instance = MagicMock()
    get_id_value_mock = MagicMock(return_value=id_)
    monkeypatch.setattr(mock_repo, "get_id_attribute_value", get_id_value_mock)
    get_mock = AsyncMock()
    monkeypatch.setattr(mock_repo, "get", get_mock)
    mock_repo.session.merge.return_value = mock_instance
    instance = await mock_repo.update(mock_instance)
    assert instance is mock_instance
    mock_repo.session.merge.assert_called_once_with(mock_instance)
    mock_repo.session.flush.assert_called_once()
    mock_repo.session.refresh.assert_called_once_with(mock_instance)
    mock_repo.session.expunge.assert_called_once_with(mock_instance)
    mock_repo.session.commit.assert_not_called()


async def test_sqlalchemy_repo_upsert(mock_repo: SQLAlchemyRepository) -> None:
    """Test the sequence of repo calls for upsert operation."""
    mock_instance = MagicMock()
    mock_repo.session.merge.return_value = mock_instance
    instance = await mock_repo.upsert(mock_instance)
    assert instance is mock_instance
    mock_repo.session.merge.assert_called_once_with(mock_instance)
    mock_repo.session.flush.assert_called_once()
    mock_repo.session.refresh.assert_called_once_with(mock_instance)
    mock_repo.session.expunge.assert_called_once_with(mock_instance)
    mock_repo.session.commit.assert_not_called()


async def test_attach_to_session_unexpected_strategy_raises_valueerror(
    mock_repo: SQLAlchemyRepository,
) -> None:
    """Test to hit the error condition in SQLAlchemy._attach_to_session()."""
    with pytest.raises(ValueError):
        await mock_repo._attach_to_session(MagicMock(), strategy="t-rex")  # type:ignore[arg-type]


async def testexecute(mock_repo: SQLAlchemyRepository) -> None:
    """Simple test of the abstraction over `AsyncSession.execute()`"""
    _ = await mock_repo._execute(mock_repo.select)
    mock_repo.session.execute.assert_called_once_with(mock_repo.select)


def test_filter_in_collection_noop_if_collection_empty(mock_repo: SQLAlchemyRepository) -> None:
    """Ensures we don't filter on an empty collection."""
    mock_repo._filter_in_collection("id", [], select=mock_repo.select)
    mock_repo.select.where.assert_not_called()


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (datetime.max, datetime.min),
        (None, datetime.min),
        (datetime.max, None),
    ],
)
def test__filter_on_datetime_field(before: datetime, after: datetime, mock_repo: SQLAlchemyRepository) -> None:
    """Test through branches of _filter_on_datetime_field()"""
    field_mock = MagicMock()
    field_mock.__gt__ = field_mock.__lt__ = lambda self, other: True
    mock_repo.model_type.updated = field_mock
    mock_repo._filter_on_datetime_field("updated", before, after, select=mock_repo.select)


def test_filter_collection_by_kwargs(mock_repo: SQLAlchemyRepository) -> None:
    """Test `filter_by()` called with kwargs."""
    _ = mock_repo.filter_collection_by_kwargs(mock_repo.select, a=1, b=2)
    mock_repo.select.filter_by.assert_called_once_with(a=1, b=2)


def test_filter_collection_by_kwargs_raises_repository_exception_for_attribute_error(
    mock_repo: SQLAlchemyRepository,
) -> None:
    """Test that we raise a repository exception if an attribute name is
    incorrect."""
    mock_repo.select.filter_by = MagicMock(  # type:ignore[assignment]
        side_effect=InvalidRequestError,
    )
    with pytest.raises(RepositoryError):
        _ = mock_repo.filter_collection_by_kwargs(mock_repo.select, a=1)


@pytest.fixture(name="engine")
async def get_sqlite_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Postgresql instance for end-to-end testing.

    Args:
        docker_ip: IP address for TCP connection to Docker containers.

    Returns:
        Async SQLAlchemy engine instance.
    """
    db_path = tempfile.mkdtemp()
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}/test.db",
        echo=True,
        poolclass=NullPool,
    )
    try:
        yield engine
    finally:
        await engine.dispose()
        Path(f"{db_path}/test.db").unlink()
        Path(db_path).rmdir()


@pytest.fixture(name="raw_authors")
def get_raw_authors() -> list[dict[str, Any]]:
    """Unstructured author representations."""
    return [
        {
            "id": UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"),
            "name": "Agatha Christie",
            "dob": "1890-09-15",
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
        },
        {
            "id": UUID("5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2"),
            "name": "Leo Tolstoy",
            "dob": "1828-09-09",
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
        },
    ]


@pytest.fixture(name="raw_books")
def get_raw_books(raw_authors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Unstructured book representations."""
    return [
        {
            "id": UUID("f34545b9-663c-4fce-915d-dd1ae9cea42a"),
            "title": "Murder on the Orient Express",
            "author_id": "97108ac1-ffcb-411d-8b1e-d9183399f63b",
            "author": raw_authors[0],
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
        },
    ]


async def _seed_db(engine: AsyncEngine, raw_authors: list[dict[str, Any]], raw_books: list[dict[str, Any]]) -> None:
    """Populate test database with sample data.

    Args:
        engine: The SQLAlchemy engine instance.
    """
    # convert date/time strings to dt objects.
    for raw_author in raw_authors:
        raw_author["dob"] = datetime.strptime(raw_author["dob"], "%Y-%m-%d")
        raw_author["created"] = datetime.strptime(raw_author["created"], "%Y-%m-%dT%H:%M:%S")
        raw_author["updated"] = datetime.strptime(raw_author["updated"], "%Y-%m-%dT%H:%M:%S")

    async with engine.begin() as conn:
        await conn.run_sync(base.orm_registry.metadata.drop_all)
        await conn.run_sync(base.orm_registry.metadata.create_all)
        await conn.execute(insert(Author).values(raw_authors))


@pytest.fixture(
    name="session",
)
async def get_sqlite_session(
    engine: AsyncEngine, raw_authors: list[dict[str, Any]], raw_books: list[dict[str, Any]]
) -> AsyncGenerator[AsyncSession, None]:
    session = async_sessionmaker(bind=engine)()
    await _seed_db(engine, raw_authors, raw_books)
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


@pytest.fixture(name="author_repo")
def get_author_repo(session: AsyncSession) -> AuthorRepository:
    return AuthorRepository(session=session)


@pytest.fixture(name="book_repo")
def get_book_repo(session: AsyncSession) -> BookRepository:
    return BookRepository(session=session)


def test_sqlite_filter_by_kwargs_with_incorrect_attribute_name(author_repo: AuthorRepository) -> None:
    with pytest.raises(RepositoryError):
        author_repo.filter_collection_by_kwargs(author_repo.select, whoops="silly me")


async def test_sqlite_repo_count_method(author_repo: AuthorRepository) -> None:
    assert await author_repo.count() == 2


async def test_sqlite_repo_list_and_count_method(
    raw_authors: list[dict[str, Any]], author_repo: AuthorRepository
) -> None:
    exp_count = len(raw_authors)
    collection, count = await author_repo.list_and_count()
    assert exp_count == count
    assert isinstance(collection, list)
    assert len(collection) == exp_count


async def test_sqlite_repo_add_method(raw_authors: list[dict[str, Any]], author_repo: AuthorRepository) -> None:
    exp_count = len(raw_authors) + 1
    new_author = Author(name="Testing", dob=datetime.now())
    obj = await author_repo.add(new_author)
    count = await author_repo.count()
    assert exp_count == count
    assert isinstance(obj, Author)
    assert new_author.name == obj.name
    assert obj.id is not None


async def test_sqlite_repo_add_many_method(raw_authors: list[dict[str, Any]], author_repo: AuthorRepository) -> None:
    exp_count = len(raw_authors) + 2
    [Author(name="Testing 2", dob=datetime.now()), Author(name="Cody", dob=datetime.now())]
    objs = await author_repo.add_many(
        [Author(name="Testing 2", dob=datetime.now()), Author(name="Cody", dob=datetime.now())]
    )
    count = await author_repo.count()
    assert exp_count == count
    assert isinstance(objs, list)
    assert len(objs) == 2
    for obj in objs:
        assert obj.id is not None
        assert obj.name in {"Testing 2", "Cody"}
