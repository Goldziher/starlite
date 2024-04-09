from advanced_alchemy import base as sa_base
from advanced_alchemy import filters as sa_filters
from advanced_alchemy import types as sa_types
from advanced_alchemy.extensions import litestar as sa_litestar

from litestar.plugins import sqlalchemy


def test_re_exports() -> None:
    assert sqlalchemy.filters is sa_filters
    assert sqlalchemy.types is sa_types

    assert sqlalchemy.AuditColumns is sa_base.AuditColumns
    assert sqlalchemy.BigIntAuditBase is sa_base.BigIntAuditBase
    assert sqlalchemy.BigIntBase is sa_base.BigIntBase
    assert sqlalchemy.BigIntPrimaryKey is sa_base.BigIntPrimaryKey
    assert sqlalchemy.CommonTableAttributes is sa_base.CommonTableAttributes
    assert sqlalchemy.UUIDAuditBase is sa_base.UUIDAuditBase
    assert sqlalchemy.UUIDBase is sa_base.UUIDBase
    assert sqlalchemy.UUIDPrimaryKey is sa_base.UUIDPrimaryKey
    assert sqlalchemy.orm_registry is sa_base.orm_registry

    assert sqlalchemy.AlembicAsyncConfig is sa_litestar.AlembicAsyncConfig
    assert sqlalchemy.AlembicCommands is sa_litestar.AlembicCommands
    assert sqlalchemy.AlembicSyncConfig is sa_litestar.AlembicSyncConfig
    assert sqlalchemy.AsyncSessionConfig is sa_litestar.AsyncSessionConfig
    assert sqlalchemy.EngineConfig is sa_litestar.EngineConfig
    assert sqlalchemy.SQLAlchemyAsyncConfig is sa_litestar.SQLAlchemyAsyncConfig
    assert sqlalchemy.SQLAlchemyDTO is sa_litestar.SQLAlchemyDTO
    assert sqlalchemy.SQLAlchemyDTOConfig is sa_litestar.SQLAlchemyDTOConfig
    assert sqlalchemy.SQLAlchemyInitPlugin is sa_litestar.SQLAlchemyInitPlugin
    assert sqlalchemy.SQLAlchemyPlugin is sa_litestar.SQLAlchemyPlugin
    assert sqlalchemy.SQLAlchemySerializationPlugin is sa_litestar.SQLAlchemySerializationPlugin
    assert sqlalchemy.SQLAlchemySyncConfig is sa_litestar.SQLAlchemySyncConfig
    assert sqlalchemy.SyncSessionConfig is sa_litestar.SyncSessionConfig
