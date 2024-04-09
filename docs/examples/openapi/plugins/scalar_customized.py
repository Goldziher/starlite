from litestar.openapi.plugins import ScalarRenderPlugin

scalar_plugin = ScalarRenderPlugin(
    js_url="https://example.com/my-custom-scalar.js",
    css_url="https://example.com/my-custom-scalar.css",
    path="/scalar",
)
