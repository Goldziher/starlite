from collections.abc import Generator
from typing import cast

import pytest
from _pytest.fixtures import FixtureRequest

from litestar.dto import AbstractDTO
from litestar.dto._backend import DTOBackend


@pytest.fixture(autouse=True)
def reset_cached_dto_backends() -> Generator[None, None, None]:
    DTOBackend._seen_model_names = set()
    AbstractDTO._dto_backends = {}
    yield
    DTOBackend._seen_model_names = set()
    AbstractDTO._dto_backends = {}


@pytest.fixture(params=[pytest.param(True, id="experimental_backend"), pytest.param(False, id="default_backend")])
def use_experimental_dto_backend(request: FixtureRequest) -> bool:
    return cast(bool, request.param)
