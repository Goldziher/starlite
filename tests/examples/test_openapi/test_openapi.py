from docs.examples.openapi import customize_pydantic_model_name

from litestar.testing import TestClient


def test_schema_generation() -> None:
    with TestClient(app=customize_pydantic_model_name.app) as client:
        assert client.app.openapi_schema.to_schema() == {
            "info": {"title": "Litestar API", "version": "1.0.0"},
            "openapi": "3.1.0",
            "servers": [{"url": "/"}],
            "paths": {
                "/id": {
                    "get": {
                        "summary": "RetrieveIdHandler",
                        "operationId": "IdRetrieveIdHandler",
                        "responses": {
                            "200": {
                                "description": "Request fulfilled, document follows",
                                "headers": {},
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/IdModel"}}},
                            }
                        },
                        "deprecated": False,
                    }
                }
            },
            "components": {
                "schemas": {
                    "IdModel": {
                        "properties": {"id": {"type": "string", "format": "uuid"}},
                        "type": "object",
                        "required": ["id"],
                        "title": "IdContainer",
                    }
                }
            },
        }


def test_customize_path() -> None:
    from docs.examples.openapi.customize_path import app

    with TestClient(app=app) as client:
        resp = client.get("/docs/openapi.json")
        assert resp.status_code == 200
