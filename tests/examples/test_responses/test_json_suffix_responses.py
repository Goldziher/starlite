from docs.examples.responses.json_suffix_responses import app

from litestar.testing import TestClient


def test_json_suffix_responses() -> None:
    with TestClient(app=app) as client:
        res = client.get("/resources")
        assert res.status_code == 418
        assert res.json() == {
            "title": "Server thinks it is a teapot",
            "type": "Server delusion",
            "status": 418,
        }
        assert res.headers["content-type"] == "application/problem+json"
