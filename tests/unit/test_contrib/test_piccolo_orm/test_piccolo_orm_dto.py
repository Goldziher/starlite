from __future__ import annotations

from decimal import Decimal
from typing import AsyncGenerator, Callable

import pytest
from polyfactory.utils.predicates import is_annotated
from typing_extensions import get_args

from litestar import Litestar
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client

try:
    import piccolo  # noqa: F401
except ImportError:
    pytest.skip("Piccolo not installed", allow_module_level=True)

import pytest
from piccolo.columns import Column, column_types
from piccolo.columns.column_types import Varchar
from piccolo.conf.apps import Finder
from piccolo.table import Table, create_db_tables, drop_db_tables

from litestar.contrib.piccolo import PiccoloDTO

from .endpoints import create_concert, retrieve_studio, retrieve_venues, studio, venues
from .tables import RecordingStudio, Venue


def test_dto_deprecation() -> None:
    class Manager(Table):
        name = Varchar(length=50)

    with pytest.deprecated_call():
        from litestar.contrib.piccolo import PiccoloDTO

        _ = PiccoloDTO[Manager]


@pytest.fixture(autouse=True)
async def scaffold_piccolo() -> AsyncGenerator:
    """Scaffolds Piccolo ORM and performs cleanup."""
    tables = Finder().get_table_classes()
    await drop_db_tables(*tables)
    await create_db_tables(*tables)
    yield
    await drop_db_tables(*tables)


def test_serializing_single_piccolo_table(scaffold_piccolo: Callable) -> None:
    with create_test_client(route_handlers=[retrieve_studio]) as client:
        response = client.get("/studio")
        assert response.status_code == HTTP_200_OK
        assert str(RecordingStudio(**response.json()).querystring) == str(studio.querystring)


def test_serializing_multiple_piccolo_tables(scaffold_piccolo: Callable) -> None:
    with create_test_client(route_handlers=[retrieve_venues]) as client:
        response = client.get("/venues")

        sanitized_venues = []
        for v in venues:
            non_secret_data = {
                column._meta.db_column_name: v[column._meta.db_column_name]
                for column in v.all_columns()
                if not column._meta.secret
            }
            sanitized_venues.append(Venue(**non_secret_data))

        assert response.status_code == HTTP_200_OK
        assert [str(Venue(**value).querystring) for value in response.json()] == [
            str(v.querystring) for v in sanitized_venues
        ]


@pytest.mark.parametrize(
    "piccolo_type, py_type, meta_data_key",
    (
        (column_types.Decimal, Decimal, None),
        (column_types.Numeric, Decimal, None),
        (column_types.Email, str, "max_length"),
        (column_types.Varchar, str, "max_length"),
        (column_types.JSON, str, "format"),
        (column_types.JSONB, str, "format"),
        (column_types.Text, str, "format"),
    ),
)
def test_piccolo_dto_type_conversion(piccolo_type: type[Column], py_type: type, meta_data_key: str | None) -> None:
    class _Table(Table):
        field = piccolo_type(required=True, help_text="my column")

    field_defs = list(PiccoloDTO.generate_field_definitions(_Table))
    assert len(field_defs) == 2
    field_def = field_defs[1]
    assert is_annotated(field_def.raw)
    assert field_def.annotation is py_type
    metadata = get_args(field_def.raw)[1]

    assert metadata.extra.get("description", "")
    if meta_data_key:
        assert metadata.extra.get(meta_data_key, "") or getattr(metadata, meta_data_key, None)


def test_piccolo_dto_openapi_spec_generation() -> None:
    app = Litestar(route_handlers=[retrieve_studio, retrieve_venues, create_concert])
    schema = app.openapi_schema

    assert schema.paths
    assert len(schema.paths) == 3
    concert_path = schema.paths["/concert"]
    assert concert_path

    studio_path = schema.paths["/studio"]
    assert studio_path

    venues_path = schema.paths["/venues"]
    assert venues_path

    post_operation = concert_path.post
    assert (
        post_operation.request_body.content["application/json"].schema.ref  # type: ignore
        == "#/components/schemas/CreateConcertConcertRequestBody"
    )

    studio_path_get_operation = studio_path.get
    assert (
        studio_path_get_operation.responses["200"].content["application/json"].schema.ref  # type: ignore
        == "#/components/schemas/RetrieveStudioRecordingStudioResponseBody"
    )

    venues_path_get_operation = venues_path.get
    assert (
        venues_path_get_operation.responses["200"].content["application/json"].schema.items.ref  # type: ignore
        == "#/components/schemas/RetrieveVenuesVenueResponseBody"
    )

    concert_schema = schema.components.schemas["CreateConcertConcertRequestBody"]
    assert concert_schema
    assert concert_schema.to_schema() == {
        "properties": {
            "band_1": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
            "band_2": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
            "venue": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
        },
        "required": [],
        "title": "CreateConcertConcertRequestBody",
        "type": "object",
    }

    record_studio_schema = schema.components.schemas["RetrieveStudioRecordingStudioResponseBody"]
    assert record_studio_schema
    assert record_studio_schema.to_schema() == {
        "properties": {
            "facilities": {"oneOf": [{"type": "null"}, {"type": "string"}]},
            "facilities_b": {"oneOf": [{"type": "null"}, {"type": "string"}]},
            "microphones": {"oneOf": [{"type": "null"}, {"items": {"type": "string"}, "type": "array"}]},
            "id": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
        },
        "required": [],
        "title": "RetrieveStudioRecordingStudioResponseBody",
        "type": "object",
    }

    venue_schema = schema.components.schemas["RetrieveVenuesVenueResponseBody"]
    assert venue_schema
    assert venue_schema.to_schema() == {
        "properties": {
            "id": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
            "name": {"oneOf": [{"type": "null"}, {"type": "string"}]},
        },
        "required": [],
        "title": "RetrieveVenuesVenueResponseBody",
        "type": "object",
    }
