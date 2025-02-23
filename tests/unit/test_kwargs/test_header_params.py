from typing import Annotated, Optional, Union

import pytest

from litestar import get, post
from litestar.params import Parameter, ParameterKwarg
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client


@pytest.mark.parametrize(
    "t_type,param_dict, param, should_raise",
    [
        (str, {"special-header": "123"}, Parameter(header="special-header", min_length=1, max_length=3), False),
        (str, {"special-header": "123"}, Parameter(header="special-header", min_length=1, max_length=2), True),
        (str, {}, Parameter(header="special-header", min_length=1, max_length=2), True),
        (
            Optional[str],
            {},
            Parameter(header="special-header", min_length=1, max_length=2, required=False, default=None),
            False,
        ),
        (int, {"special-header": "123"}, Parameter(header="special-header", ge=100, le=201), False),
        (int, {"special-header": "123"}, Parameter(header="special-header", ge=100, le=120), True),
        (int, {}, Parameter(header="special-header", ge=100, le=120), True),
        (Optional[int], {}, Parameter(header="special-header", ge=100, le=120, required=False, default=None), False),
    ],
)
def test_header_params(
    t_type: Optional[Union[str, int]], param_dict: dict[str, str], param: ParameterKwarg, should_raise: bool
) -> None:
    test_path = "/test"

    @get(path=test_path)
    def test_method(special_header: t_type = param) -> None:  # type: ignore[valid-type]
        if special_header:
            assert special_header in (param_dict.get("special-header"), int(param_dict.get("special-header")))  # type: ignore[arg-type]

    with create_test_client(test_method) as client:
        response = client.get(test_path, headers=param_dict)
        if should_raise:
            assert response.status_code == HTTP_400_BAD_REQUEST, response.json()
        else:
            assert response.status_code == HTTP_200_OK, response.json()


def test_header_param_with_post() -> None:
    # https://github.com/litestar-org/litestar/issues/3734
    @post()
    async def handler(data: str, secret: Annotated[str, Parameter(header="x-secret")]) -> None:
        return None

    with create_test_client([handler], raise_server_exceptions=True) as client:
        assert client.post("/", json={}).status_code == 400
