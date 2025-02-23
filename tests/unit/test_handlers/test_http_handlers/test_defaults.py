from typing import Any

import pytest

from litestar import HttpMethod
from litestar.handlers.http_handlers import HTTPRouteHandler
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT


@pytest.mark.parametrize(
    "http_method, expected_status_code",
    [
        (HttpMethod.POST, HTTP_201_CREATED),
        (HttpMethod.DELETE, HTTP_204_NO_CONTENT),
        (HttpMethod.GET, HTTP_200_OK),
        (HttpMethod.HEAD, HTTP_200_OK),
        (HttpMethod.PUT, HTTP_200_OK),
        (HttpMethod.PATCH, HTTP_200_OK),
        ([HttpMethod.POST], HTTP_201_CREATED),
        ([HttpMethod.DELETE], HTTP_204_NO_CONTENT),
        ([HttpMethod.GET], HTTP_200_OK),
        ([HttpMethod.HEAD], HTTP_200_OK),
        ([HttpMethod.PUT], HTTP_200_OK),
        ([HttpMethod.PATCH], HTTP_200_OK),
        ("POST", HTTP_201_CREATED),
        ("DELETE", HTTP_204_NO_CONTENT),
        ("GET", HTTP_200_OK),
        ("HEAD", HTTP_200_OK),
        ("PUT", HTTP_200_OK),
        ("PATCH", HTTP_200_OK),
        (["POST"], HTTP_201_CREATED),
        (["DELETE"], HTTP_204_NO_CONTENT),
        (["GET"], HTTP_200_OK),
        (["HEAD"], HTTP_200_OK),
        (["PUT"], HTTP_200_OK),
        (["PATCH"], HTTP_200_OK),
    ],
)
def test_route_handler_default_status_code(http_method: Any, expected_status_code: int) -> None:
    route_handler = HTTPRouteHandler(http_method=http_method, fn=lambda: None)
    assert route_handler.status_code == expected_status_code
