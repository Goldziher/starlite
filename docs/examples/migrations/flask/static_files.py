from litestar import Litestar
from litestar.static_files import StaticFilesConfig

app = Litestar([], static_files_config=[StaticFilesConfig(path="/static", directories=["static"])])
