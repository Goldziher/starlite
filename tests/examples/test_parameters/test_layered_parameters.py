from typing import Any

import pytest
from docs.examples.parameters.layered_parameters import app

from litestar.testing import TestClient


@pytest.mark.parametrize(
    "params,status_code,expected",
    [
        (
            {
                "headers": {"MyHeader": "foo"},
                "cookies": {"special-cookie": "bar"},
                "params": {"controller_param": "11", "local_param": "foo"},
            },
            200,
            {"controller_param": 11, "local_param": "foo", "path_param": 11, "router_param": "foo"},
        ),
        (
            {
                "cookies": {"special-cookie": "bar"},
                "params": {"controller_param": "11", "local_param": "foo"},
            },
            400,
            None,
        ),
        (
            {
                "headers": {"MyHeader": "foo"},
                "cookies": {"special-cookie": "bar"},
                "params": {"controller_param": "11"},
            },
            400,
            None,
        ),
        (
            {
                "headers": {"MyHeader": "foo"},
                "cookies": {"special-cookie": "bar"},
                "params": {"local_param": "foo"},
            },
            400,
            None,
        ),
    ],
)
def test_layered_parameters(params: dict[str, Any], status_code: int, expected: dict[str, Any]) -> None:
    with TestClient(app=app) as client:
        client.cookies = params.pop("cookies")
        response = client.get("/router/controller/11", **params)
        assert response.status_code == status_code, response.json()
        if expected:
            assert response.json() == expected
