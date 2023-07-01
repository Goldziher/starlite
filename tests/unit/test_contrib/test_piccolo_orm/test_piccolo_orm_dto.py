from typing import AsyncGenerator, Callable

import pytest
from piccolo.conf.apps import Finder
from piccolo.table import create_db_tables, drop_db_tables
from piccolo.testing.model_builder import ModelBuilder

from litestar import Litestar
from litestar.contrib.piccolo.dto import PiccoloDTO
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from litestar.testing import create_test_client

from .endpoints import create_concert, retrieve_studio, retrieve_venues, studio, venues
from .tables import Band, Concert, Manager, RecordingStudio, Venue


@pytest.fixture()
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
        assert response.status_code == HTTP_200_OK
        assert [str(Venue(**value).querystring) for value in response.json()] == [str(v.querystring) for v in venues]


async def test_create_piccolo_table_instance(scaffold_piccolo: Callable, anyio_backend: str) -> None:
    manager = await ModelBuilder.build(Manager)
    band_1 = await ModelBuilder.build(Band, defaults={Band.manager: manager})
    band_2 = await ModelBuilder.build(Band, defaults={Band.manager: manager})
    venue = await ModelBuilder.build(Venue)
    concert = ModelBuilder.build_sync(
        Concert, persist=False, defaults={Concert.band_1: band_1, Concert.band_2: band_2, Concert.venue: venue}
    )

    with create_test_client(route_handlers=[create_concert], dto=PiccoloDTO) as client:
        data = concert.to_dict()
        data["band_1"] = band_1.id  # type: ignore[attr-defined]
        data["band_2"] = band_2.id  # type: ignore[attr-defined]
        data["venue"] = venue.id  # type: ignore[attr-defined]
        response = client.post("/concert", json=data)
        assert response.status_code == HTTP_201_CREATED


def test_piccolo_dto_openapi_spec_generation() -> None:
    app = Litestar(route_handlers=[retrieve_studio, retrieve_venues, create_concert], dto=PiccoloDTO)
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
        == "#/components/schemas/tests.unit.test_contrib.test_piccolo_orm.tables.ConcertRequestBody"
    )

    studio_path_get_operation = studio_path.get
    assert (
        studio_path_get_operation.responses["200"].content["application/json"].schema.ref  # type: ignore
        == "#/components/schemas/tests.unit.test_contrib.test_piccolo_orm.tables.RecordingStudioResponseBody"
    )

    venues_path_get_operation = venues_path.get
    assert (
        venues_path_get_operation.responses["200"].content["application/json"].schema.items.ref  # type: ignore
        == "#/components/schemas/tests.unit.test_contrib.test_piccolo_orm.tables.Venue"
    )

    concert_schema = schema.components.schemas["tests.unit.test_contrib.test_piccolo_orm.tables.ConcertRequestBody"]  # type: ignore
    assert concert_schema
    assert concert_schema.to_schema() == {
        "properties": {
            "band_1": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
            "band_2": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
            "venue": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
        },
        "required": [],
        "title": "tests.unit.test_contrib.test_piccolo_orm.tables.ConcertRequestBody",
        "type": "object",
    }

    record_studio_schema = schema.components.schemas["tests.unit.test_contrib.test_piccolo_orm.tables.RecordingStudioResponseBody"]  # type: ignore
    assert record_studio_schema
    assert record_studio_schema.to_schema() == {
        "properties": {
            "facilities": {"oneOf": [{"type": "null"}, {"type": "string"}]},
            "facilities_b": {"oneOf": [{"type": "null"}, {"type": "string"}]},
            "id": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
        },
        "required": [],
        "title": "tests.unit.test_contrib.test_piccolo_orm.tables.RecordingStudioResponseBody",
        "type": "object",
    }

    venue_schema = schema.components.schemas["tests.unit.test_contrib.test_piccolo_orm.tables.Venue"]  # type: ignore
    assert venue_schema
    assert venue_schema.to_schema() == {
        "properties": {
            "capacity": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
            "id": {"oneOf": [{"type": "null"}, {"type": "integer"}]},
            "name": {"oneOf": [{"type": "null"}, {"type": "string"}]},
        },
        "required": [],
        "title": "tests.unit.test_contrib.test_piccolo_orm.tables.Venue",
        "type": "object",
    }
