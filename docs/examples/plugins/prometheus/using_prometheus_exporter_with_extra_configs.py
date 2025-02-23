from typing import Any

from litestar import Litestar, Request
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController


# We can modify the path of our custom handler and override the metrics format by subclassing the PrometheusController.
class CustomPrometheusController(PrometheusController):
    path = "/custom-path"
    openmetrics_format = True


# Let's assume this as our extra custom labels which we want our metrics to have.
# The values can be either a string or a callable that returns a string.
def custom_label_callable(request: Request[Any, Any, Any]) -> str:
    return "v2.0"


extra_labels = {
    "version_no": custom_label_callable,
    "location": "earth",
}

# Customizing the buckets for the histogram.
buckets = [0.1, 0.2, 0.3, 0.4, 0.5]


# Adding exemplars to the metrics.
# Note that this supported only in openmetrics format.
def custom_exemplar(request: Request[Any, Any, Any]) -> dict[str, str]:
    return {"trace_id": "1234"}


# Creating the instance of PrometheusConfig with our own custom options.
# The given options are not necessary, you can use the default ones
# as well by just creating a raw instance PrometheusConfig()
prometheus_config = PrometheusConfig(
    app_name="litestar-example",
    prefix="litestar",
    labels=extra_labels,
    buckets=buckets,  # pyright: ignore[reportArgumentType]
    exemplars=custom_exemplar,
    excluded_http_methods=["POST"],
)


# Creating the litestar app instance with our custom PrometheusConfig and PrometheusController.
app = Litestar(route_handlers=[CustomPrometheusController], middleware=[prometheus_config.middleware])
