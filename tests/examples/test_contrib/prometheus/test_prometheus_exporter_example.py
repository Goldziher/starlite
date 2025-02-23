from typing import Any

import pytest
from prometheus_client import REGISTRY

from litestar import Controller, Litestar, Request, get
from litestar.plugins.prometheus import PrometheusMiddleware
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient


def clear_collectors() -> None:
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)

    PrometheusMiddleware._metrics = {}


@pytest.mark.parametrize(
    "group_path, route_path, route_template, expected_path",
    [
        (True, "/test/litestar", "test/litestar", "/test/litestar"),
        (False, "/test/litestar", "test/litestar", "/test/litestar"),
        (True, "/test/litestar", "test/{name:str}", "/test/{name}"),
        (False, "/test/litestar", "test/{name:str}", "/test/litestar"),
        (
            True,
            "/project/123a/team/abc/test/hi",
            "project/{project:str}/team/{team:str}/test/{name:str}",
            "/project/{project}/team/{team}/test/{name}",
        ),
        (
            False,
            "/project/123a/team/abc/test/hi",
            "project/{project:str}/team/{team:str}/test/{name:str}",
            "/project/123a/team/abc/test/hi",
        ),
    ],
)
def test_prometheus_exporter_example(
    group_path: bool, route_path: str, route_template: str, expected_path: str
) -> None:
    from docs.examples.plugins.prometheus.using_prometheus_exporter import create_app

    app = create_app(group_path=group_path)

    clear_collectors()

    @get(route_template)
    def home(name: str) -> dict[str, Any]:
        return {"hello": name}

    app.register(home)

    with TestClient(app) as client:
        client.get(route_path)
        metrics_exporter_response = client.get("/metrics")

        assert metrics_exporter_response.status_code == HTTP_200_OK
        metrics = metrics_exporter_response.content.decode()
        assert expected_path in metrics


def test_correct_population_path_template() -> None:
    class TestController(Controller):
        path = "/prefix"

        @get("/{id_:int}")
        async def b(self, request: Request, id_: int) -> str:
            return request.scope["path_template"]

        @get("/{id_:int}/postfix")
        async def a(self, request: Request, id_: int) -> str:
            return request.scope["path_template"]

    app = Litestar([TestController])

    with TestClient(app) as client:
        without_postfix_resp = client.get("/prefix/1")
        with_postfix_resp = client.get("/prefix/1/postfix")

        assert without_postfix_resp.content.decode() == "/prefix/{id_}"
        assert with_postfix_resp.content.decode() == "/prefix/{id_}/postfix"
