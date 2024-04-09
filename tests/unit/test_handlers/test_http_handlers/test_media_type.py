from enum import Enum
from typing import Any, AnyStr

import pytest

from litestar import Litestar, MediaType, get
from tests.models import DataclassPerson


class MyEnum(Enum):
    first = 1


class MyBytes(bytes): ...


class CustomStrEnum(str, Enum):
    foo = "FOO"


@pytest.mark.parametrize(
    "annotation, expected_media_type",
    (
        (str, MediaType.TEXT),
        (bytes, MediaType.TEXT),
        (AnyStr, MediaType.TEXT),
        (MyBytes, MediaType.TEXT),
        (CustomStrEnum, MediaType.TEXT),
        (MyEnum, MediaType.JSON),
        (dict, MediaType.JSON),
        (DataclassPerson, MediaType.JSON),
    ),
)
def test_media_type_inference(annotation: Any, expected_media_type: MediaType) -> None:
    @get("/")
    def handler() -> annotation:
        return None

    Litestar(route_handlers=[handler])

    handler.on_registration(Litestar())
    assert handler.media_type == expected_media_type
