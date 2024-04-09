from litestar.openapi.plugins import RedocRenderPlugin

redoc_plugin = RedocRenderPlugin(version="next", google_fonts=True, path="/redoc")
