from typing import Any, Tuple, cast

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
from litestar.contrib.opentelemetry import OpenTelemetryConfig
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


def create_config(**kwargs: Any) -> Tuple[OpenTelemetryConfig, InMemoryMetricReader, InMemorySpanExporter]:
    """Create OpenTelemetryConfig, an InMemoryMetricReader and InMemorySpanExporter.

    Args:
        **kwargs: Any config kwargs to pass to the OpenTelemetryConfig constructor.

    Returns:
        A tuple containing an OpenTelemetryConfig, an InMemoryMetricReader and InMemorySpanExporter.
    """
    resource = Resource(attributes={SERVICE_NAME: "litestar-test"})
    tracer_provider = TracerProvider(resource=resource)
    exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))

    aggregation_last_value = {Counter: ExplicitBucketHistogramAggregation()}
    reader = InMemoryMetricReader(preferred_aggregation=aggregation_last_value)  # type: ignore[arg-type]
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])

    set_meter_provider(meter_provider)

    meter = get_meter_provider().get_meter("litestar-test")

    return (
        OpenTelemetryConfig(tracer_provider=tracer_provider, meter=meter, **kwargs),
        reader,
        exporter,
    )


def test_open_telemetry_middleware_with_http_route() -> None:
    config, reader, exporter = create_config()

    @get("/")
    def handler() -> dict:
        return {"hello": "world"}

    with create_test_client(handler, middleware=[config.middleware]) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert reader.get_metrics_data()

        first_span, second_span, third_span = cast("Tuple[Span, Span, Span]", exporter.get_finished_spans())
        assert dict(first_span.attributes) == {"http.status_code": 200, "type": "http.response.start"}  # type: ignore[arg-type]
        assert dict(second_span.attributes) == {"type": "http.response.body"}  # type: ignore[arg-type]
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
            "http.route": "handler",
            "http.status_code": 200,
        }

        metric_data = reader.get_metrics_data()
        assert metric_data.resource_metrics

        resource_metrics = metric_data.resource_metrics[0]
        assert resource_metrics.scope_metrics

        scope_metrics = resource_metrics.scope_metrics[0]
        assert scope_metrics.metrics

        request_metric = scope_metrics.metrics[0]
        assert len(list(request_metric.data.data_points)) == 1


def test_open_telemetry_middleware_with_websocket_route() -> None:
    config, reader, exporter = create_config()

    @websocket("/")
    async def handler(socket: "WebSocket") -> None:
        await socket.accept()
        await socket.send_json({"hello": "world"})
        await socket.close()

    with create_test_client(handler, middleware=[config.middleware]).websocket_connect("/") as client:
        data = client.receive_json()
        assert data == {"hello": "world"}

        first_span, second_span, third_span, fourth_span, fifth_span = cast(
            "Tuple[Span, Span, Span, Span, Span]", exporter.get_finished_spans()
        )
        assert dict(first_span.attributes) == {"type": "websocket.connect"}  # type: ignore[arg-type]
        assert dict(second_span.attributes) == {"type": "websocket.accept"}  # type: ignore[arg-type]
        assert dict(third_span.attributes) == {"http.status_code": 200, "type": "websocket.send"}  # type: ignore[arg-type]
        assert dict(fourth_span.attributes) == {"type": "websocket.close"}  # type: ignore[arg-type]
        assert dict(fifth_span.attributes) == {  # type: ignore[arg-type]
            "http.scheme": "ws",
            "http.host": "testserver",
            "net.host.port": 80,
            "http.target": "/",
            "http.url": "ws://testserver/",
            "http.server_name": "testserver",
            "http.user_agent": "testclient",
            "net.peer.ip": "testclient",
            "net.peer.port": 50000,
            "http.route": "handler",
            "http.status_code": 200,
        }
