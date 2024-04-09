APP_FILE_CONTENT = """
from litestar import Litestar
app = Litestar([])
"""


CREATE_APP_FILE_CONTENT = """
from litestar import Litestar

def create_app():
    return Litestar([])


def func():
    return False
"""


GENERIC_APP_FACTORY_FILE_CONTENT = """
from litestar import Litestar

def any_name() -> Litestar:
    return Litestar([])


def func():
    return False
"""

GENERIC_APP_FACTORY_FILE_CONTENT_STRING_ANNOTATION = """
from litestar import Litestar

def any_name() -> "Litestar":
    return Litestar([])


def func():
    return False
"""


GENERIC_APP_FACTORY_FILE_CONTENT_FUTURE_ANNOTATIONS = """
from __future__ import annotations

from litestar import Litestar

def any_name() -> Litestar:
    return Litestar([])


def func():
    return False
"""


APP_FACTORY_FILE_CONTENT_SERVER_LIFESPAN_PLUGIN = """
from contextlib import contextmanager
from typing import Generator

from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.plugins.base import CLIPlugin


class StartupPrintPlugin(CLIPlugin):

    @contextmanager
    def server_lifespan(self, app: Litestar) -> Generator[None, None, None]:
        print("i_run_before_startup_plugin")  # noqa: T201
        try:
            yield
        finally:
            print("i_run_after_shutdown_plugin")  # noqa: T201

def create_app() -> Litestar:
    return Litestar(route_handlers=[], plugins=[StartupPrintPlugin()])

"""
APP_FILE_CONTENT_ROUTES_EXAMPLE = """
from litestar import Litestar, get
from litestar.openapi import OpenAPIConfig
from typing import Dict


@get("/")
def hello_world() -> Dict[str, str]:
    return {"hello": "world"}


@get("/foo")
def foo() -> str:
    return "bar"


@get("/schema/all/foo/bar/schema/")
def long_api() -> Dict[str, str]:
    return {"test": "api"}



app = Litestar(
    openapi_config=OpenAPIConfig(
        title="test_app",
        version="0",
        path="/api-docs",
    ),
    route_handlers=[hello_world, foo, long_api]
)

"""
