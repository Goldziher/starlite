from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, Type, Union, cast
from uuid import uuid4

import pytest
from _pytest.fixtures import FixtureRequest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from litestar.contrib.sqlalchemy import base
from litestar.repository.exceptions import ConflictError, RepositoryError
from litestar.repository.filters import LimitOffset
from litestar.repository.testing.generic_mock_repository import (
    GenericAsyncMockRepository,
    GenericSyncMockRepository,
)
from tests.helpers import maybe_async
from tests.unit.test_repository.models_uuid import UUIDAuthor, UUIDBook

AuthorRepository = GenericAsyncMockRepository[UUIDAuthor]
AuthorRepositoryType = Type[AuthorRepository]
ModelType = Type[Union[base.UUIDBase, base.BigIntBase]]
AuditModelType = Type[Union[base.UUIDAuditBase, base.BigIntAuditBase]]


class CreateAuditModelFixture(Protocol):
    def __call__(self, extra_columns: dict[str, type[Mapped] | Mapped] | None = None) -> AuditModelType: ...


@pytest.fixture(name="authors")
def fx_authors() -> list[UUIDAuthor]:
    """Collection of Author models."""
    return [
        UUIDAuthor(id=uuid4(), name=name, dob=dob, created_at=datetime.min, updated_at=datetime.min)
        for name, dob in [("Agatha Christie", date(1890, 9, 15)), ("Leo Tolstoy", date(1828, 9, 9))]
    ]


@pytest.fixture(params=[GenericAsyncMockRepository, GenericSyncMockRepository], ids=["async", "sync"])
def repository_type(request: FixtureRequest) -> type[GenericAsyncMockRepository]:
    return cast("type[GenericAsyncMockRepository]", request.param)


@pytest.fixture(name="author_repository_type", params=[GenericAsyncMockRepository, GenericSyncMockRepository])
def fx_author_repository_type(
    authors: list[UUIDAuthor], monkeypatch: pytest.MonkeyPatch, repository_type: type[GenericAsyncMockRepository]
) -> AuthorRepositoryType:
    """Mock Author repository, pre-seeded with collection data."""
    repo = repository_type[UUIDAuthor]  # type: ignore[index]
    repo.seed_collection(authors)
    return cast("type[GenericAsyncMockRepository]", repo)


@pytest.fixture(name="author_repository")
def fx_author_repository(
    author_repository_type: type[GenericAsyncMockRepository[UUIDAuthor]],
) -> GenericAsyncMockRepository[UUIDAuthor]:
    """Mock Author repository instance."""
    return author_repository_type()


@pytest.fixture(params=[base.UUIDBase, base.BigIntBase])
def model_type(request: FixtureRequest) -> ModelType:
    return cast(ModelType, type(f"{request.node.nodeid}Model", (request.param,), {}))


@pytest.fixture(params=[base.UUIDAuditBase, base.BigIntAuditBase])
def create_audit_model_type(request: FixtureRequest) -> CreateAuditModelFixture:
    def create(extra_columns: dict[str, type[Mapped] | Mapped] | None = None) -> AuditModelType:
        return cast(AuditModelType, type(f"{request.node.nodeid}AuditModel", (request.param,), extra_columns or {}))

    return create


@pytest.fixture()
def audit_model_type(create_audit_model_type: CreateAuditModelFixture) -> AuditModelType:
    return create_audit_model_type()


async def test_repo_raises_conflict_if_add_with_id(
    authors: list[UUIDAuthor], author_repository: AuthorRepository
) -> None:
    """Test mock repo raises conflict if add identified entity."""
    with pytest.raises(ConflictError):
        await maybe_async(author_repository.add(authors[0]))


async def test_repo_raises_conflict_if_add_many_with_id(
    authors: list[UUIDAuthor], author_repository: AuthorRepository
) -> None:
    """Test mock repo raises conflict if add identified entity."""
    with pytest.raises(ConflictError):
        await maybe_async(author_repository.add_many(authors))


def test_generic_mock_repository_parametrization(repository_type: type[GenericAsyncMockRepository]) -> None:
    """Test that the mock repository handles multiple types."""
    author_repo = repository_type[UUIDAuthor]  # type: ignore[index]
    book_repo = repository_type[UUIDBook]  # type: ignore[index]
    assert author_repo.model_type is UUIDAuthor
    assert book_repo.model_type is UUIDBook


def test_generic_mock_repository_seed_collection(author_repository_type: AuthorRepositoryType) -> None:
    """Test seeding instances."""
    author_repository_type.seed_collection([UUIDAuthor(id="abc")])
    assert "abc" in author_repository_type.collection


def test_generic_mock_repository_clear_collection(author_repository_type: AuthorRepositoryType) -> None:
    """Test clearing collection for type."""
    author_repository_type.clear_collection()
    assert not author_repository_type.collection


def test_generic_mock_repository_filter_collection_by_kwargs(author_repository: AuthorRepository) -> None:
    """Test filtering the repository collection by kwargs."""
    collection = author_repository.filter_collection_by_kwargs(author_repository.collection, name="Leo Tolstoy")
    assert len(collection) == 1
    assert next(iter(collection.values())).name == "Leo Tolstoy"


def test_generic_mock_repository_filter_collection_by_kwargs_and_semantics(author_repository: AuthorRepository) -> None:
    """Test that filtering by kwargs has `AND` semantics when multiple kwargs,
    not `OR`."""
    collection = author_repository.filter_collection_by_kwargs(
        author_repository.collection, name="Agatha Christie", dob="1828-09-09"
    )
    assert len(collection) == 0


def test_generic_mock_repository_raises_repository_exception_if_named_attribute_doesnt_exist(
    author_repository: AuthorRepository,
) -> None:
    """Test that a repo exception is raised if a named attribute doesn't
    exist."""
    with pytest.raises(RepositoryError):
        _ = author_repository.filter_collection_by_kwargs(author_repository.collection, cricket="ball")


async def test_sets_created_updated_on_add(
    repository_type: type[GenericAsyncMockRepository], audit_model_type: AuditModelType
) -> None:
    """Test that the repository updates the 'created_at' and 'updated_at' timestamps
    if necessary."""

    instance = audit_model_type()
    assert "created_at" not in vars(instance)
    assert "updated_at" not in vars(instance)

    instance = await maybe_async(repository_type[audit_model_type]().add(instance))  # type: ignore[index]
    assert "created_at" in vars(instance)
    assert "updated_at" in vars(instance)


async def test_sets_updated_on_update(author_repository: AuthorRepository) -> None:
    """Test that the repository updates the 'updated' timestamp if
    necessary."""

    instance = next(iter(author_repository.collection.values()))
    original_updated = instance.updated_at
    instance = await maybe_async(author_repository.update(instance))
    assert instance.updated_at > original_updated


async def test_does_not_set_created_updated(
    repository_type: type[GenericAsyncMockRepository], model_type: ModelType
) -> None:
    """Test that the repository does not update the 'updated' timestamps when
    appropriate."""

    instance = model_type()
    repo = repository_type[model_type]()  # type: ignore[index]
    assert "created_at" not in vars(instance)
    assert "updated_at" not in vars(instance)

    instance = await maybe_async(repo.add(instance))
    assert "created_at" not in vars(instance)
    assert "updated_at" not in vars(instance)

    instance = await maybe_async(repo.update(instance))
    assert "created_at" not in vars(instance)
    assert "updated_at" not in vars(instance)


async def test_add(repository_type: type[GenericAsyncMockRepository], model_type: ModelType) -> None:
    """Test that the repository add method works correctly."""

    instance = model_type()

    inserted_uuid_instance = await maybe_async(repository_type[model_type]().add(instance))  # type: ignore[index]
    assert inserted_uuid_instance == instance


async def test_add_many(repository_type: type[GenericAsyncMockRepository], model_type: ModelType) -> None:
    """Test that the repository add_many method works correctly."""

    instances = [model_type(), model_type()]

    inserted_uuid_instances = await maybe_async(repository_type[model_type]().add_many(instances))  # type: ignore[index]

    assert len(instances) == len(inserted_uuid_instances)


async def test_update(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository update method works correctly."""

    Model = create_audit_model_type({"random_column": Mapped[str]})

    mock_repo = repository_type[Model]()  # type: ignore[index]

    instance = await maybe_async(mock_repo.add(Model(random_column="A")))
    instance.random_column = "B"
    updated_instance = await maybe_async(mock_repo.update(instance))

    assert updated_instance == instance


async def test_update_many(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository add_many method works correctly."""

    Model = create_audit_model_type({"random_column": Mapped[str]})

    mock_repo = repository_type[Model]()  # type: ignore[index]
    instances = [Model(random_column="A"), Model(random_column="B")]
    inserted_instances = await maybe_async(mock_repo.add_many(instances))
    for instance in inserted_instances:
        instance.random_column = "C"
    updated_instances = await maybe_async(mock_repo.update_many(instances))
    for instance in updated_instances:
        assert instance.random_column == "C"
    assert len(instances) == len(updated_instances)


async def test_upsert(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository upsert method works correctly."""

    Model = create_audit_model_type({"random_column": Mapped[str]})

    mock_repo = repository_type[Model]()  # type: ignore[index]

    instance = await maybe_async(mock_repo.upsert(Model(random_column="A")))
    instance.random_column = "B"
    updated_instance = await maybe_async(mock_repo.upsert(instance))

    assert updated_instance == instance


async def test_upsert_many(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository upsert method works correctly."""

    Model = create_audit_model_type({"random_column": Mapped[str]})

    mock_repo = repository_type[Model]()  # type: ignore[index]

    instance = await maybe_async(mock_repo.upsert(Model(random_column="A")))
    instance.random_column = "B"
    new_instance = Model(random_column="C")
    updated_instances = await maybe_async(mock_repo.upsert_many([instance, new_instance]))

    assert new_instance in updated_instances
    assert instance in updated_instances


async def test_list(repository_type: type[GenericAsyncMockRepository], audit_model_type: AuditModelType) -> None:
    """Test that the repository list returns records."""

    mock_repo = repository_type[audit_model_type]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many([audit_model_type(), audit_model_type()]))
    listed_instances = await maybe_async(mock_repo.list())
    assert inserted_instances == listed_instances


async def test_delete(repository_type: type[GenericAsyncMockRepository], audit_model_type: AuditModelType) -> None:
    """Test that the repository delete functionality."""

    mock_repo = repository_type[audit_model_type]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many([audit_model_type(), audit_model_type()]))
    delete_instance = await maybe_async(mock_repo.delete(inserted_instances[0].id))
    assert delete_instance.id == inserted_instances[0].id
    count = await maybe_async(mock_repo.count())
    assert count == 1


async def test_delete_many(repository_type: type[GenericAsyncMockRepository], audit_model_type: AuditModelType) -> None:
    """Test that the repository delete many functionality."""

    mock_repo = repository_type[audit_model_type]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many([audit_model_type(), audit_model_type()]))
    delete_instances = await maybe_async(mock_repo.delete_many([obj.id for obj in inserted_instances]))
    assert len(delete_instances) == 2
    count = await maybe_async(mock_repo.count())
    assert count == 0


async def test_list_and_count(
    repository_type: type[GenericAsyncMockRepository], audit_model_type: AuditModelType
) -> None:
    """Test that the repository list_and_count returns records and the total record count."""

    instances = [audit_model_type(), audit_model_type()]
    mock_repo = repository_type[audit_model_type]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many(instances))
    listed_instances, count = await maybe_async(mock_repo.list_and_count())
    assert inserted_instances == listed_instances
    assert count == len(instances)


async def test_exists(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository exists returns booleans."""

    Model = create_audit_model_type({"random_column": Mapped[str]})

    instances = [Model(random_column="value 1"), Model(random_column="value 2")]
    mock_repo = repository_type[Model]()  # type: ignore[index]
    _ = await maybe_async(mock_repo.add_many(instances))
    exists = await maybe_async(mock_repo.exists(random_column="value 1"))
    assert exists


async def test_exists_with_filter(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository exists returns booleans. with filter argument"""
    limit_filter = LimitOffset(limit=1, offset=0)

    Model = create_audit_model_type({"random_column": Mapped[str]})

    instances = [Model(random_column="value 1"), Model(random_column="value 2")]
    mock_repo = repository_type[Model]()  # type: ignore[index]
    _ = await maybe_async(mock_repo.add_many(instances))
    exists = await maybe_async(mock_repo.exists(limit_filter, random_column="value 1"))
    assert exists


async def test_count(repository_type: type[GenericAsyncMockRepository], audit_model_type: AuditModelType) -> None:
    """Test that the repository count returns the total record count."""

    instances = [audit_model_type(), audit_model_type()]
    mock_repo = repository_type[audit_model_type]()  # type: ignore[index]
    _ = await maybe_async(mock_repo.add_many(instances))
    count = await maybe_async(mock_repo.count())
    assert count == len(instances)


async def test_get(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository get returns a model record correctly."""

    Model = create_audit_model_type({"random_column": Mapped[str]})

    instances = [Model(random_column="value 1"), Model(random_column="value 2")]
    mock_repo = repository_type[Model]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many(instances))
    item_id = inserted_instances[0].id
    fetched_instance = await maybe_async(mock_repo.get(item_id))
    assert inserted_instances[0] == fetched_instance


async def test_get_one(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository get_one returns a model record correctly."""

    Model = create_audit_model_type({"random_column": Mapped[str]})

    instances = [Model(random_column="value 1"), Model(random_column="value 2")]
    mock_repo = repository_type[Model]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many(instances))
    fetched_instance = await maybe_async(mock_repo.get_one(random_column="value 1"))
    assert inserted_instances[0] == fetched_instance
    with pytest.raises(RepositoryError):
        _ = await maybe_async(mock_repo.get_one(random_column="value 3"))


async def test_get_one_or_none(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository get_one_or_none returns a model record correctly."""

    Model = create_audit_model_type({"random_column": Mapped[str]})

    instances = [Model(random_column="value 1"), Model(random_column="value 2")]
    mock_repo = repository_type[Model]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many(instances))
    fetched_instance = await maybe_async(mock_repo.get_one_or_none(random_column="value 1"))
    assert inserted_instances[0] == fetched_instance
    none_instance = await maybe_async(mock_repo.get_one_or_none(random_column="value 3"))
    assert none_instance is None


async def test_get_or_create(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository get_or_create returns a model record correctly."""

    Model = create_audit_model_type(
        {"random_column": Mapped[str], "cool_attribute": mapped_column(String, nullable=True)}
    )

    instances = [Model(random_column="value 1", cool_attribute="yep"), Model(random_column="value 2")]
    mock_repo = repository_type[Model]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many(instances))
    fetched_instance, fetched_created = await maybe_async(mock_repo.get_or_create(random_column="value 2"))
    assert await maybe_async(mock_repo.count()) == 2
    assert inserted_instances[1] == fetched_instance
    assert fetched_created is False
    _, created = await maybe_async(mock_repo.get_or_create(random_column="value 3"))
    assert await maybe_async(mock_repo.count()) == 3
    assert created


async def test_get_or_create_match_fields(
    repository_type: type[GenericAsyncMockRepository], create_audit_model_type: CreateAuditModelFixture
) -> None:
    """Test that the repository get_or_create returns a model record correctly."""

    Model = create_audit_model_type(
        {"random_column": Mapped[str], "cool_attribute": mapped_column(String, nullable=True)}
    )

    instances = [Model(random_column="value 1", cool_attribute="yep"), Model(random_column="value 2")]
    mock_repo = repository_type[Model]()  # type: ignore[index]
    inserted_instances = await maybe_async(mock_repo.add_many(instances))
    fetched_instance, fetched_created = await maybe_async(
        mock_repo.get_or_create(match_fields=["random_column"], random_column="value 1", cool_attribute="other thing")
    )
    assert await maybe_async(mock_repo.count()) == 2
    assert inserted_instances[0] == fetched_instance
    assert fetched_created is False
