from docs.examples.plugins.di_plugin import app

from litestar.testing import TestClient


def test_di_plugin_example() -> None:
    with TestClient(app) as client:
        res = client.get("/?param=hello")
        assert res.status_code == 200
        assert res.text == "hello"
