from typing import cast

import pytest
from _pytest.fixtures import FixtureRequest
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk.metrics._internal import MeterProvider
from opentelemetry.sdk.metrics._internal.aggregation import (
    ExplicitBucketHistogramAggregation,
)
from opentelemetry.sdk.metrics._internal.export import InMemoryMetricReader
from opentelemetry.sdk.metrics._internal.instrument import Counter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from litestar import WebSocket, get, websocket
from litestar.config.app import AppConfig
from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin
from litestar.exceptions import http_exceptions
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client
from litestar.types.asgi_types import ASGIApp, Receive, Scope, Send


@pytest.fixture(scope="session")
def resource() -> Resource:
    return Resource(attributes={SERVICE_NAME: "litestar-test"})


@pytest.fixture(scope="session")
def reader() -> InMemoryMetricReader:
    aggregation_last_value = {Counter: ExplicitBucketHistogramAggregation()}
    return InMemoryMetricReader(preferred_aggregation=aggregation_last_value)  # type: ignore[arg-type]


@pytest.fixture(scope="session")
def meter_provider(resource: Resource, reader: InMemoryMetricReader) -> MeterProvider:
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    set_meter_provider(provider)
    return provider


@pytest.fixture()
def exporter() -> InMemorySpanExporter:
    return InMemorySpanExporter()


@pytest.fixture()
def config(
    resource: Resource, exporter: InMemorySpanExporter, meter_provider: MeterProvider, request: FixtureRequest
) -> OpenTelemetryConfig:
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    meter = get_meter_provider().get_meter(f"litestar-test-{request.node.nodeid}")
    return OpenTelemetryConfig(tracer_provider=tracer_provider, meter=meter)


@pytest.fixture(params=["middleware", "plugin"])
def app_config(request: FixtureRequest, config: OpenTelemetryConfig) -> AppConfig:
    if request.param == "middleware":
        return AppConfig(middleware=[config.middleware])
    return AppConfig(plugins=[OpenTelemetryPlugin(config)])


def test_open_telemetry_middleware_with_http_route(
    app_config: AppConfig,
    reader: InMemoryMetricReader,
    exporter: InMemorySpanExporter,
) -> None:
    @get("/")
    def handler() -> dict:
        return {"hello": "world"}

    with create_test_client(handler, middleware=app_config.middleware, plugins=app_config.plugins) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert reader.get_metrics_data()

        first_span, second_span, third_span = cast("tuple[Span, Span, Span]", exporter.get_finished_spans())
        assert dict(first_span.attributes) == {"http.status_code": 200, "asgi.event.type": "http.response.start"}  # type: ignore[arg-type]
        assert dict(second_span.attributes) == {"asgi.event.type": "http.response.body"}  # type: ignore[arg-type]
        assert dict(third_span.attributes) == {  # type: ignore[arg-type]
            "http.scheme": "http",
            "http.host": "testserver.local",
            "net.host.port": 80,
            "http.flavor": "1.1",
            "http.target": "/",
            "http.url": "http://testserver.local/",
            "http.method": "GET",
            "http.server_name": "testserver.local",
            "http.user_agent": "testclient",
            "net.peer.ip": "testclient",
            "net.peer.port": 50000,
            "http.route": "GET /",
            "http.status_code": 200,
        }

        metric_data = reader.get_metrics_data()
        assert metric_data
        assert metric_data.resource_metrics

        resource_metrics = metric_data.resource_metrics[0]
        assert resource_metrics.scope_metrics

        scope_metrics = resource_metrics.scope_metrics[0]
        assert scope_metrics.metrics

        request_metric = scope_metrics.metrics[0]
        assert len(list(request_metric.data.data_points)) == 1


def test_open_telemetry_middleware_with_websocket_route(
    app_config: AppConfig,
    reader: InMemoryMetricReader,
    exporter: InMemorySpanExporter,
) -> None:
    @websocket("/")
    async def handler(socket: "WebSocket") -> None:
        await socket.accept()
        await socket.send_json({"hello": "world"})
        await socket.close()

    with create_test_client(handler, middleware=app_config.middleware, plugins=app_config.plugins).websocket_connect(
        "/"
    ) as client:
        data = client.receive_json()
        assert data == {"hello": "world"}

        first_span, second_span, third_span, fourth_span, fifth_span = cast(
            "tuple[Span, Span, Span, Span, Span]", exporter.get_finished_spans()
        )
        assert dict(first_span.attributes) == {"asgi.event.type": "websocket.connect"}  # type: ignore[arg-type]
        assert dict(second_span.attributes) == {"asgi.event.type": "websocket.accept"}  # type: ignore[arg-type]
        assert dict(third_span.attributes) == {"asgi.event.type": "websocket.send", "http.status_code": 200}  # type: ignore[arg-type]
        assert dict(fourth_span.attributes) == {"asgi.event.type": "websocket.close"}  # type: ignore[arg-type]
        assert dict(fifth_span.attributes) == {  # type: ignore[arg-type]
            "http.scheme": "ws",
            "http.host": "testserver.local",
            "net.host.port": 80,
            "http.target": "/",
            "http.url": "ws://testserver.local/",
            "http.server_name": "testserver.local",
            "http.user_agent": "testclient",
            "net.peer.ip": "testclient",
            "net.peer.port": 50000,
            "http.route": "/",
            "http.status_code": 200,
        }


def test_open_telemetry_middleware_handles_route_not_found_under_span_http(
    app_config: AppConfig,
    reader: InMemoryMetricReader,
    exporter: InMemorySpanExporter,
) -> None:
    @get("/")
    def handler() -> dict:
        raise Exception("random Exception")

    with create_test_client(handler, middleware=app_config.middleware, plugins=app_config.plugins) as client:
        response = client.get("/route_that_does_not_exist")
        assert response.status_code

        first_span, second_span, third_span = cast("tuple[Span, Span, Span]", exporter.get_finished_spans())
        assert dict(first_span.attributes) == {  # type: ignore[arg-type]
            "http.status_code": 404,
            "asgi.event.type": "http.response.start",
        }
        assert dict(second_span.attributes) == {"asgi.event.type": "http.response.body"}  # type: ignore[arg-type]
        assert dict(third_span.attributes) == {  # type: ignore[arg-type]
            "http.scheme": "http",
            "http.host": "testserver.local",
            "net.host.port": 80,
            "http.flavor": "1.1",
            "http.target": "/route_that_does_not_exist",
            "http.url": "http://testserver.local/route_that_does_not_exist",
            "http.method": "GET",
            "http.server_name": "testserver.local",
            "http.user_agent": "testclient",
            "net.peer.ip": "testclient",
            "net.peer.port": 50000,
            "http.route": "GET /route_that_does_not_exist",
            "http.status_code": 404,
        }


def test_open_telemetry_middleware_handles_method_not_allowed_under_span_http(
    app_config: AppConfig,
    reader: InMemoryMetricReader,
    exporter: InMemorySpanExporter,
) -> None:
    @get("/")
    def handler() -> dict:
        raise Exception("random Exception")

    with create_test_client(handler, middleware=app_config.middleware, plugins=app_config.plugins) as client:
        response = client.post("/")
        assert response.status_code

        first_span, second_span, third_span = cast("tuple[Span, Span, Span]", exporter.get_finished_spans())
        assert dict(first_span.attributes) == {  # type: ignore[arg-type]
            "http.status_code": 405,
            "asgi.event.type": "http.response.start",
        }
        assert dict(second_span.attributes) == {"asgi.event.type": "http.response.body"}  # type: ignore[arg-type]
        assert dict(third_span.attributes) == {  # type: ignore[arg-type]
            "http.scheme": "http",
            "http.host": "testserver.local",
            "net.host.port": 80,
            "http.flavor": "1.1",
            "http.target": "/",
            "http.url": "http://testserver.local/",
            "http.method": "POST",
            "http.server_name": "testserver.local",
            "http.user_agent": "testclient",
            "net.peer.ip": "testclient",
            "net.peer.port": 50000,
            "http.route": "POST /",
            "http.status_code": 405,
        }


def test_open_telemetry_middleware_handles_errors_caused_on_middleware(
    app_config: AppConfig,
    reader: InMemoryMetricReader,
    exporter: InMemorySpanExporter,
) -> None:
    raise_exception = True

    def middleware_factory(app: ASGIApp) -> ASGIApp:
        async def error_middleware(scope: Scope, receive: Receive, send: Send) -> None:
            if raise_exception:
                raise http_exceptions.NotAuthorizedException()
            await app(scope, receive, send)

        return error_middleware

    @get("/")
    def handler() -> dict:
        raise Exception("random Exception")

    with create_test_client(
        handler, middleware=[middleware_factory, *app_config.middleware], plugins=app_config.plugins
    ) as client:
        response = client.get("/")
        assert response.status_code

        first_span, second_span, third_span = cast("tuple[Span, Span, Span]", exporter.get_finished_spans())
        assert dict(first_span.attributes) == {  # type: ignore[arg-type]
            "http.status_code": 401,
            "asgi.event.type": "http.response.start",
        }
        assert dict(second_span.attributes) == {"asgi.event.type": "http.response.body"}  # type: ignore[arg-type]
        assert dict(third_span.attributes) == {  # type: ignore[arg-type]
            "http.scheme": "http",
            "http.host": "testserver.local",
            "net.host.port": 80,
            "http.flavor": "1.1",
            "http.target": "/",
            "http.url": "http://testserver.local/",
            "http.method": "GET",
            "http.server_name": "testserver.local",
            "http.user_agent": "testclient",
            "net.peer.ip": "testclient",
            "net.peer.port": 50000,
            "http.route": "GET /",
            "http.status_code": 401,
        }
