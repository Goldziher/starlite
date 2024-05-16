from starlette.applications import Starlette
from starlette.routing import Route


async def index(request): ...


routes = [Route("/", endpoint=index)]

app = Starlette(routes=routes)
