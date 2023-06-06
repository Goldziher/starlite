"""Unit tests for the SQLAlchemy Repository implementation for psycopg."""
from __future__ import annotations

from asyncio import AbstractEventLoop, get_event_loop_policy
from pathlib import Path
from typing import Any, Generator, Iterator

import pytest
from sqlalchemy import Engine, NullPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from tests.contrib.sqlalchemy.models_bigint import (
    AuthorSyncRepository,
    BookSyncRepository,
)
from tests.contrib.sqlalchemy.repository import sqlalchemy_sync_bigint_tests as st


@pytest.mark.sqlalchemy_duckdb
@pytest.fixture(scope="session")
def event_loop() -> Iterator[AbstractEventLoop]:
    """Need the event loop scoped to the session so that we can use it to check
    containers are ready in session scoped containers fixture."""
    policy = get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.sqlalchemy_duckdb
@pytest.fixture(name="engine")
def fx_engine(tmp_path: Path) -> Generator[Engine, None, None]:
    """SQLite engine for end-to-end testing.

    Returns:
        Async SQLAlchemy engine instance.
    """
    engine = create_engine(
        f"duckdb:///{tmp_path}/test.duck.db",
        echo=True,
        poolclass=NullPool,
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.mark.sqlalchemy_duckdb
@pytest.fixture(
    name="session",
)
def fx_session(
    engine: Engine,
    raw_authors_bigint: list[dict[str, Any]],
    raw_books_bigint: list[dict[str, Any]],
    raw_rules_bigint: list[dict[str, Any]],
) -> Generator[Session, None, None]:
    session = sessionmaker(bind=engine)()
    st.seed_db(engine, raw_authors_bigint, raw_books_bigint, raw_rules_bigint)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.mark.sqlalchemy_duckdb
@pytest.fixture(name="author_repo")
def fx_author_repo(session: Session) -> AuthorSyncRepository:
    return AuthorSyncRepository(session=session)


@pytest.mark.sqlalchemy_duckdb
@pytest.fixture(name="book_repo")
def fx_book_repo(session: Session) -> BookSyncRepository:
    return BookSyncRepository(session=session)


@pytest.mark.sqlalchemy_duckdb
def test_filter_by_kwargs_with_incorrect_attribute_name(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy filter by kwargs with invalid column name.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_filter_by_kwargs_with_incorrect_attribute_name(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_count_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy count.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_count_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_list_and_count_method(
    raw_authors_bigint: list[dict[str, Any]], author_repo: AuthorSyncRepository
) -> None:
    """Test SQLALchemy list with count.

    Args:
        raw_authors_bigint (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_list_and_count_method(raw_authors_bigint=raw_authors_bigint, author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_list_and_count_method_empty(book_repo: BookSyncRepository) -> None:
    """Test SQLALchemy list with count.

    Args:
        raw_authors_bigint (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
    """

    st.test_repo_list_and_count_method_empty(book_repo=book_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_list_method(raw_authors_bigint: list[dict[str, Any]], author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy list.

    Args:
        raw_authors_bigint (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_list_method(raw_authors_bigint=raw_authors_bigint, author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_add_method(raw_authors_bigint: list[dict[str, Any]], author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy list.

    Args:
        raw_authors_bigint (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_add_method(raw_authors_bigint=raw_authors_bigint, author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_add_many_method(raw_authors_bigint: list[dict[str, Any]], author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Add Many.

    Args:
        raw_authors_bigint (list[dict[str, Any]]): list of authors pre-seeded into the mock repository
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_add_many_method(raw_authors_bigint=raw_authors_bigint, author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_update_many_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Update Many.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_update_many_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_exists_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy exists.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_exists_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_update_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Update.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_update_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_delete_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy delete.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_delete_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_delete_many_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy delete many.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_delete_many_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_get_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Get.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_get_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_get_one_or_none_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Get One.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_get_one_or_none_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_get_one_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Get One.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_get_one_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_get_or_create_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Get or create.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_get_or_create_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_get_or_create_match_filter(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Get or create with a match filter

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_get_or_create_match_filter(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_upsert_method(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy upsert.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_upsert_method(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_filter_before_after(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy BeforeAfter filter.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_filter_before_after(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_filter_search(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Search filter.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_filter_search(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_filter_order_by(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Order By filter.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_filter_order_by(author_repo=author_repo)


@pytest.mark.sqlalchemy_duckdb
def test_repo_filter_collection(author_repo: AuthorSyncRepository) -> None:
    """Test SQLALchemy Collection filter.

    Args:
        author_repo (AuthorRepository): The author mock repository
    """
    st.test_repo_filter_collection(author_repo=author_repo)
