import re
import time
from http.client import HTTPException
from pathlib import Path
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch
from prometheus_client import REGISTRY
from pytest_mock import MockerFixture

from litestar import get, post, websocket_listener
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController, PrometheusMiddleware
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


def create_config(**kwargs: Any) -> PrometheusConfig:
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)

    PrometheusMiddleware._metrics = {}
    return PrometheusConfig(**kwargs)


def test_prometheus_exporter_metrics_with_http() -> None:
    config = create_config()

    @get("/duration")
    def duration_handler() -> dict:
        time.sleep(0.1)
        return {"hello": "world"}

    @get("/error")
    def handler_error() -> dict:
        raise HTTPException("Error Occurred")

    with create_test_client(
        [duration_handler, handler_error, PrometheusController], middleware=[config.middleware]
    ) as client:
        client.get("/error")
        client.get("/duration")
        metrics_exporter_response = client.get("/metrics")

        assert metrics_exporter_response.status_code == HTTP_200_OK
        metrics = metrics_exporter_response.content.decode()

        assert (
            """litestar_request_duration_seconds_sum{app_name="litestar",method="GET",path="/duration",status_code="200"}"""
            in metrics
        )

        assert (
            """litestar_requests_error_total{app_name="litestar",method="GET",path="/error",status_code="500"} 1.0"""
            in metrics
        )

        assert (
            """litestar_request_duration_seconds_bucket{app_name="litestar",le="0.005",method="GET",path="/error",status_code="500"} 1.0"""
            in metrics
        )

        assert (
            """litestar_requests_in_progress{app_name="litestar",method="GET",path="/metrics",status_code="200"} 1.0"""
            in metrics
        )

        assert (
            """litestar_requests_in_progress{app_name="litestar",method="GET",path="/duration",status_code="200"} 0.0"""
            in metrics
        )

        duration_metric_matches = re.findall(
            r"""litestar_request_duration_seconds_sum{app_name="litestar",method="GET",path="/duration",status_code="200"} (\d+\.\d+)""",
            metrics,
        )

        assert duration_metric_matches != []
        assert round(float(duration_metric_matches[0]), 1) == 0.1

        client.get("/duration")
        metrics = client.get("/metrics").content.decode()

        assert (
            """litestar_requests_total{app_name="litestar",method="GET",path="/duration",status_code="200"} 2.0"""
            in metrics
        )

        assert (
            """litestar_requests_in_progress{app_name="litestar",method="GET",path="/error",status_code="200"} 0.0"""
            in metrics
        )

        assert (
            """litestar_requests_in_progress{app_name="litestar",method="GET",path="/metrics",status_code="200"} 1.0"""
            in metrics
        )


def test_prometheus_middleware_configurations() -> None:
    labels = {"foo": "bar", "baz": lambda a: "qux"}

    config = create_config(
        app_name="litestar_test",
        prefix="litestar_rocks",
        labels=labels,
        buckets=[0.1, 0.5, 1.0],
        excluded_http_methods=["POST"],
    )

    @get("/test")
    def test() -> dict:
        return {"hello": "world"}

    @post("/ignore")
    def ignore() -> dict:
        return {"hello": "world"}

    with create_test_client([test, ignore, PrometheusController], middleware=[config.middleware]) as client:
        client.get("/test")
        client.post("/ignore")
        metrics_exporter_response = client.get("/metrics")

        assert metrics_exporter_response.status_code == HTTP_200_OK
        metrics = metrics_exporter_response.content.decode()

        assert (
            """litestar_rocks_requests_total{app_name="litestar_test",baz="qux",foo="bar",method="GET",path="/test",status_code="200"} 1.0"""
            in metrics
        )

        assert (
            """litestar_rocks_requests_total{app_name="litestar_test",baz="qux",foo="bar",method="POST",path="/ignore",status_code="201"} 1.0"""
            not in metrics
        )

        assert (
            """litestar_rocks_request_duration_seconds_bucket{app_name="litestar_test",baz="qux",foo="bar",le="0.1",method="GET",path="/test",status_code="200"} 1.0"""
            in metrics
        )

        assert (
            """litestar_rocks_request_duration_seconds_bucket{app_name="litestar_test",baz="qux",foo="bar",le="0.5",method="GET",path="/test",status_code="200"} 1.0"""
            in metrics
        )

        assert (
            """litestar_rocks_request_duration_seconds_bucket{app_name="litestar_test",baz="qux",foo="bar",le="1.0",method="GET",path="/test",status_code="200"} 1.0"""
            in metrics
        )


def test_prometheus_controller_configurations() -> None:
    config = create_config(
        exemplars=lambda a: {"trace_id": "1234"},
    )

    class CustomPrometheusController(PrometheusController):
        path: str = "/metrics/custom"
        openmetrics_format: bool = True

    @get("/test")
    def test() -> dict:
        return {"hello": "world"}

    with create_test_client([test, CustomPrometheusController], middleware=[config.middleware]) as client:
        client.get("/test")

        metrics_exporter_response = client.get("/metrics/custom")

        assert metrics_exporter_response.status_code == HTTP_200_OK
        metrics = metrics_exporter_response.content.decode()

        assert (
            """litestar_requests_total{app_name="litestar",method="GET",path="/test",status_code="200"} 1.0 # {trace_id="1234"} 1.0"""
            in metrics
        )


def test_prometheus_with_websocket() -> None:
    config = create_config()

    @websocket_listener("/test")
    def test(data: str) -> dict:
        return {"hello": data}

    with create_test_client([test, PrometheusController], middleware=[config.middleware]) as client:
        with client.websocket_connect("/test") as websocket:
            websocket.send_text("litestar")
            websocket.receive_json()

        metrics_exporter_response = client.get("/metrics")

        assert metrics_exporter_response.status_code == HTTP_200_OK
        metrics = metrics_exporter_response.content.decode()

        assert (
            """litestar_requests_total{app_name="litestar",method="websocket",path="/test",status_code="200"} 1.0"""
            in metrics
        )


@pytest.mark.parametrize("env_var", ["PROMETHEUS_MULTIPROC_DIR", "prometheus_multiproc_dir"])
def test_procdir(monkeypatch: MonkeyPatch, tmp_path: Path, mocker: MockerFixture, env_var: str) -> None:
    proc_dir = tmp_path / "something"
    proc_dir.mkdir()
    monkeypatch.setenv(env_var, str(proc_dir))
    config = create_config()
    mock_registry = mocker.patch("litestar.plugins.prometheus.controller.CollectorRegistry")
    mock_collector = mocker.patch("litestar.plugins.prometheus.controller.multiprocess.MultiProcessCollector")

    with create_test_client([PrometheusController], middleware=[config.middleware]) as client:
        client.get("/metrics")

    mock_collector.assert_called_once_with(mock_registry.return_value)
