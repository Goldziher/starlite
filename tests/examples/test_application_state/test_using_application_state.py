from logging import INFO
from typing import Any

import pytest
from docs.examples.application_state.using_application_state import app

from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient


@pytest.mark.usefixtures("reset_httpx_logging")
def test_using_application_state(caplog: Any) -> None:
    with (
        caplog.at_level(INFO, "docs.examples.application_state.using_application_state"),
        TestClient(app=app) as client,
    ):
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

    assert {record.getMessage() for record in caplog.records} == {
        "state value in middleware: abc123",
        "state value in dependency: abc123",
        "state value in handler from `State`: abc123",
        "state value in handler from `Request`: abc123",
    }
