from typing import Annotated, Optional

import pytest

from litestar import get, post
from litestar.params import Parameter, ParameterKwarg
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client


@pytest.mark.parametrize(
    "t_type,param_dict,param,expected_code",
    [
        (
            Optional[str],
            {},
            Parameter(cookie="special-cookie", min_length=1, max_length=2, required=False, default=None),
            HTTP_200_OK,
        ),
        (int, {"special-cookie": "123"}, Parameter(cookie="special-cookie", ge=100, le=201), HTTP_200_OK),
        (int, {"special-cookie": "123"}, Parameter(cookie="special-cookie", ge=100, le=120), HTTP_400_BAD_REQUEST),
        (int, {}, Parameter(cookie="special-cookie", ge=100, le=120), HTTP_400_BAD_REQUEST),
        (
            Optional[int],
            {},
            Parameter(cookie="special-cookie", ge=100, le=120, required=False, default=None),
            HTTP_200_OK,
        ),
    ],
)
def test_cookie_params(t_type: type, param_dict: dict, param: ParameterKwarg, expected_code: int) -> None:
    test_path = "/test"

    @get(path=test_path)
    def test_method(special_cookie: t_type = param) -> None:  # type: ignore[valid-type]
        if special_cookie:
            assert special_cookie in (param_dict.get("special-cookie"), int(param_dict.get("special-cookie")))  # type: ignore[arg-type]

    with create_test_client(test_method) as client:
        # Set cookies on the client to avoid warnings about per-request cookies.
        client.cookies = param_dict  # type: ignore[assignment]
        response = client.get(test_path)
        assert response.status_code == expected_code, response.json()


def test_cookie_param_with_post() -> None:
    # https://github.com/litestar-org/litestar/issues/3734
    @post()
    async def handler(data: str, secret: Annotated[str, Parameter(cookie="x-secret")]) -> None:
        return None

    with create_test_client([handler], raise_server_exceptions=True) as client:
        assert client.post("/", json={}).status_code == 400
