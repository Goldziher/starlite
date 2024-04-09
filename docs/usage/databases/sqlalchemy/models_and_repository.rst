SQLAlchemy Models & Repository
==============================

Litestar comes with a built-in repository class
(:class:`SQLAlchemyAsyncRepository <advanced_alchemy.repository.SQLAlchemyAsyncRepository>`)
for `SQLAlchemy <https://docs.sqlalchemy.org/>`_ to make CRUD operations easier.

Features
--------

* Pre-configured ``DeclarativeBase`` for :doc:`SQLAlchemy <sqlalchemy:index>` 2.0 that includes a
  UUID or Big Integer based primary-key,
  a  `sentinel column <https://docs.sqlalchemy.org/en/20/core/connections.html#configuring-sentinel-columns>`_, and
  an optional version with audit columns.
* Generic synchronous and asynchronous repositories for select, insert, update, and delete operations on SQLAlchemy models
* Implements optimized methods for bulk inserts, updates, and deletes and uses `lambda_stmt <https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.lambda_stmt>`_ when possible.
* Integrated counts, pagination, sorting, filtering with ``LIKE``, ``IN``, and dates before and/or after.
* Tested support for multiple database backends including:

  - SQLite via `aiosqlite <https://aiosqlite.omnilib.dev/en/stable/>`_ or `sqlite <https://docs.python.org/3/library/sqlite3.html>`_
  - Postgres via `asyncpg <https://magicstack.github.io/asyncpg/current/>`_ or `psycopg3 (async or sync) <https://www.psycopg.org/psycopg3/>`_
  - MySQL via `asyncmy <https://github.com/long2ice/asyncmy>`_
  - Oracle via `oracledb <https://oracle.github.io/python-oracledb/>`_
  - Google Spanner via `spanner-sqlalchemy <https://github.com/googleapis/python-spanner-sqlalchemy/>`_
  - DuckDB via `duckdb_engine <https://github.com/Mause/duckdb_engine>`_
  - Microsoft SQL Server via `pyodbc <https://github.com/mkleehammer/pyodbc>`_

Basic Use
---------

To use the :class:`SQLAlchemyAsyncRepository <advanced_alchemy.repository.SQLAlchemyAsyncRepository>`
repository, you must first define your models using one of the included built-in ``DeclarativeBase`` ORM base
implementations:

* :class:`UUIDBase <advanced_alchemy.base.UUIDBase>`
* :class:`UUIDAuditBase <advanced_alchemy.base.UUIDAuditBase>`

Both include a ``UUID`` based primary key
and ``UUIDAuditBase`` includes an ``updated_at`` and ``created_at`` timestamp column.

The ``UUID`` will be a native ``UUID``/``GUID`` type on databases that support it such as Postgres.  For other engines without
a native UUID data type, the UUID is stored as a 16-byte ``BYTES`` or ``RAW`` field.

* :class:`BigIntBase <advanced_alchemy.base.BigIntBase>`
* :class:`BigIntAuditBase <advanced_alchemy.base.BigIntAuditBase>`

Both include a ``BigInteger`` based primary key
and ``BigIntAuditBase`` includes an ``updated_at`` and ``created_at`` timestamp column.

Models using these bases also include the following enhancements:

* Auto-generated snake-case table name from class name
* Pydantic BaseModel and Dict classes map to an optimized JSON type that is
  :class:`JSONB <sqlalchemy.dialects.postgresql.JSONB>` for Postgres,
  `VARCHAR` or `BYTES` with JSON check constraint for Oracle, and
  :class:`JSON <sqlalchemy.types.JSON>` for other dialects.

.. literalinclude:: /examples/contrib/sqlalchemy/sqlalchemy_declarative_models.py
    :caption: sqlalchemy_declarative_models.py
    :language: python

Basic Controller Integration
-----------------------------

Once you have declared your models, you are ready to use the ``SQLAlchemyAsyncRepository`` class with
your controllers and function based routes.

.. literalinclude:: /examples/contrib/sqlalchemy/sqlalchemy_async_repository.py
    :caption: sqlalchemy_async_repository.py
    :language: python

Alternately, you may use the ``SQLAlchemySyncRepository`` class for your synchronous database connection.

.. literalinclude:: /examples/contrib/sqlalchemy/sqlalchemy_sync_repository.py
    :caption: sqlalchemy_sync_repository.py
    :language: python

.. seealso::

    * :doc:`/tutorials/repository-tutorial/index`
