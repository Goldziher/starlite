"""Unit tests for the SQLAlchemy Repository implementation."""
from __future__ import annotations

from asyncio import AbstractEventLoop, get_event_loop_policy
from pathlib import Path
from typing import Any, AsyncGenerator, Iterator

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tests.contrib.sqlalchemy.models import AuthorRepository, BookRepository, IngredientRepository, StoreRepository
from tests.contrib.sqlalchemy.repository import sqlalchemy_tests as st


# we need to override these for sqlite.  It doesnt force you to use the identity column and does not autogenerate this way.
@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(name="raw_ingredients")
def fx_raw_ingredients() -> list[dict[str, Any]]:
    """Unstructured ingredients representations."""
    return [{"id": 1, "name": "Apple"}, {"id": 2, "name": "Orange"}]


@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(name="raw_stores")
def fx_raw_stores() -> list[dict[str, Any]]:
    """Unstructured store representations."""
    return [
        {
            "id": 1,
            "store_name": "Super Market - Talladega, AL",
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
        },
        {
            "id": 2,
            "store_name": "Corner Store - Moody, AL",
            "created": "0001-01-01T00:00:00",
            "updated": "0001-01-01T00:00:00",
        },
    ]


@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(scope="session")
def event_loop() -> Iterator[AbstractEventLoop]:
    """Need the event loop scoped to the session so that we can use it to check
    containers are ready in session scoped containers fixture."""
    policy = get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(name="engine")
async def fx_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    """SQLite engine for end-to-end testing.

    Returns:
        Async SQLAlchemy engine instance.
    """
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path}/test.db",
        echo=True,
        poolclass=NullPool,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(
    name="session",
)
async def fx_session(
    engine: AsyncEngine,
    raw_authors: list[dict[str, Any]],
    raw_books: list[dict[str, Any]],
    raw_stores: list[dict[str, Any]],
    raw_ingredients: list[dict[str, Any]],
) -> AsyncGenerator[AsyncSession, None]:
    session = async_sessionmaker(bind=engine)()
    await st.seed_db(engine, raw_authors, raw_books, raw_stores, raw_ingredients)
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(name="author_repo")
def fx_author_repo(session: AsyncSession) -> AuthorRepository:
    return AuthorRepository(session=session)


@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(name="book_repo")
def fx_book_repo(session: AsyncSession) -> BookRepository:
    return BookRepository(session=session)


@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(name="store_repo")
def fx_store_repo(session: AsyncSession) -> StoreRepository:
    return StoreRepository(session=session)


@pytest.mark.sqlalchemy_aiosqlite
@pytest.fixture(name="ingredient_repo")
def fx_ingredient_repo(session: AsyncSession) -> IngredientRepository:
    return IngredientRepository(session=session)


@pytest.mark.sqlalchemy_aiosqlite
def test_filter_by_kwargs_with_incorrect_attribute_name(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy filter by kwargs with invalid column name.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_filter_by_kwargs_with_incorrect_attribute_name(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_count_method(author_repo: AuthorRepository, store_repo: StoreRepository) -> None:
    """Test SQLALchemy count.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_count_method(author_repo=author_repo, store_repo=store_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_list_and_count_method(
    raw_authors: list[dict[str, Any]],
    author_repo: AuthorRepository,
    raw_stores: list[dict[str, Any]],
    store_repo: StoreRepository,
) -> None:
    """Test SQLALchemy list with count.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
        raw_stores (list[dict[str, Any]]): list of stores pre-seeded into the mock repository
        store_repo (StoreRepository): The store mock repository
    """
    await st.test_repo_list_and_count_method(
        raw_authors=raw_authors, author_repo=author_repo, raw_stores=raw_stores, store_repo=store_repo
    )


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_list_and_count_method_empty(book_repo: BookRepository) -> None:
    """Test SQLALchemy list with count.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
    """

    await st.test_repo_list_and_count_method_empty(book_repo=book_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_list_method(
    raw_authors: list[dict[str, Any]],
    author_repo: AuthorRepository,
    raw_stores: list[dict[str, Any]],
    store_repo: StoreRepository,
) -> None:
    """Test SQLALchemy list.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
        raw_stores (list[dict[str, Any]]): list of stores pre-seeded into the mock repository
        store_repo (StoreRepository): The store mock repository
    """
    await st.test_repo_list_method(
        raw_authors=raw_authors, author_repo=author_repo, raw_stores=raw_stores, store_repo=store_repo
    )


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_add_method(
    raw_authors: list[dict[str, Any]],
    author_repo: AuthorRepository,
    raw_stores: list[dict[str, Any]],
    store_repo: StoreRepository,
) -> None:
    """Test SQLALchemy list.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
        raw_stores (list[dict[str, Any]]): list of stores pre-seeded into the mock repository
        store_repo (StoreRepository): The store mock repository
    """
    await st.test_repo_add_method(
        raw_authors=raw_authors, author_repo=author_repo, raw_stores=raw_stores, store_repo=store_repo
    )


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_add_many_method(raw_authors: list[dict[str, Any]], author_repo: AuthorRepository) -> None:
    """Test SQLALchemy Add Many.

    Args:
        raw_authors (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_add_many_method(raw_authors=raw_authors, author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_update_many_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy Update Many.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_update_many_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_exists_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy exists.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_exists_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_update_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy Update.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_update_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_delete_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy delete.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_delete_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_delete_many_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy delete many.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_delete_many_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_get_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy Get.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_get_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_get_one_or_none_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy Get One.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_get_one_or_none_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_get_one_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy Get One.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_get_one_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_get_or_create_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy Get or create.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_get_or_create_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_get_or_create_match_filter(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy Get or create with a match filter

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_get_or_create_match_filter(author_repo=author_repo)


@pytest.mark.sqlalchemy_aiosqlite
async def test_repo_upsert_method(author_repo: AuthorRepository) -> None:
    """Test SQLALchemy upsert.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    await st.test_repo_upsert_method(author_repo=author_repo)
