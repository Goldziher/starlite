from litestar import Litestar
from litestar.config.compression import CompressionConfig

app = Litestar(
    route_handlers=[...],
    compression_config=CompressionConfig(backend="gzip", gzip_compress_level=9),
)
