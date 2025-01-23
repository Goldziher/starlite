import asyncio
import pdb  # noqa: T100
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

# Install this packages if you want to run this test-app
import ipdb  # pyright: ignore  # noqa: T100
import pdbr  # pyright: ignore
import pudb  # pyright: ignore  # noqa: T100
import uvicorn

from litestar import Litestar, get


@get("/")
async def zero_division_error() -> Dict[str, str]:
    """Handler function that returns a greeting dictionary."""
    1 / 0  # pyright: ignore # noqa: B018  
    return {"message": "ZeroDevisionError didn't occur."}


pdb_app = Litestar(route_handlers=[zero_division_error], pdb_on_exception=True, debugger_module=pdb)
ipdb_app = Litestar(route_handlers=[zero_division_error], pdb_on_exception=True, debugger_module=ipdb)
pudb_app = Litestar(route_handlers=[zero_division_error], pdb_on_exception=True, debugger_module=pudb)
pdbr_app = Litestar(route_handlers=[zero_division_error], pdb_on_exception=True, debugger_module=pdbr)


def run_server(app, port):
    uvicorn.run(app, port=port)


async def start_servers():
    with ThreadPoolExecutor() as executor:
        # Run all the servers concurrently
        await asyncio.gather(
            asyncio.get_event_loop().run_in_executor(executor, run_server, pdb_app, 8000),
            asyncio.get_event_loop().run_in_executor(executor, run_server, ipdb_app, 8001),
            asyncio.get_event_loop().run_in_executor(executor, run_server, pudb_app, 8002),
            asyncio.get_event_loop().run_in_executor(executor, run_server, pdbr_app, 8003),
        )


if __name__ == "__main__":
    asyncio.run(start_servers())
