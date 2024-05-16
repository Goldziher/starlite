from litestar import Litestar, get, post
from litestar.config.csrf import CSRFConfig


@get()
async def get_resource() -> str:
    # GET is one of the safe methods
    return "some_resource"


@post("{id:int}")
async def create_resource(id: int) -> bool:
    # POST is one of the unsafe methods
    return True


csrf_config = CSRFConfig(secret="my-secret")

app = Litestar([get_resource, create_resource], csrf_config=csrf_config)
