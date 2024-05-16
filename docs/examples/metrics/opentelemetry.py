from litestar import Litestar
from litestar.contrib.opentelemetry import OpenTelemetryConfig

open_telemetry_config = OpenTelemetryConfig()

app = Litestar(middleware=[open_telemetry_config.middleware])
