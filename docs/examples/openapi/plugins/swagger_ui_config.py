from litestar.openapi.plugins import SwaggerRenderPlugin

swagger_plugin = SwaggerRenderPlugin(version="5.1.3", path="/swagger")
