from unittest.mock import patch

import pytest
from orjson import JSONDecodeError

from starlite.connection import Request


@pytest.mark.asyncio  # type: ignore
async def test_request_empty_body_to_json() -> None:
    with patch.object(Request, "body", return_value=b""):
        request_empty_payload: Request = Request(scope={"type": "http"})
        request_json = await request_empty_payload.json()
        assert request_json is None


@pytest.mark.asyncio  # type: ignore
async def test_request_invalid_body_to_json() -> None:
    with patch.object(Request, "body", return_value=b"invalid"), pytest.raises(JSONDecodeError):
        request_empty_payload: Request = Request(scope={"type": "http"})
        await request_empty_payload.json()


@pytest.mark.asyncio  # type: ignore
async def test_request_valid_body_to_json() -> None:
    with patch.object(Request, "body", return_value=b'{"test": "valid"}'):
        request_empty_payload: Request = Request(scope={"type": "http"})
        request_json = await request_empty_payload.json()
        assert request_json == {"test": "valid"}
