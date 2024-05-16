from litestar import Litestar
from litestar.config.cors import CORSConfig

cors_config = CORSConfig(allow_origins=["https://www.example.com"])

app = Litestar(route_handlers=[...], cors_config=cors_config)
