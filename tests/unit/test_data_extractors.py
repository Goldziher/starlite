from typing import Any, List
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockFixture

from litestar import Request
from litestar.connection.base import empty_receive
from litestar.data_extractors import ConnectionDataExtractor, ResponseDataExtractor
from litestar.datastructures import Cookie
from litestar.enums import RequestEncodingType
from litestar.response.base import ASGIResponse
from litestar.status_codes import HTTP_200_OK
from litestar.testing import RequestFactory

factory = RequestFactory()


async def test_connection_data_extractor() -> None:
    request = factory.post(
        path="/a/b/c",
        headers={"Common": "abc", "Special": "123", "Content-Type": "application/json; charset=utf-8"},
        cookies=[Cookie(key="regular"), Cookie(key="auth")],
        query_params={"first": ["1", "2", "3"], "second": ["jeronimo"]},
        data={"hello": "world"},
    )
    request.scope["path_params"] = {"first": "10", "second": "20", "third": "30"}
    extractor = ConnectionDataExtractor(parse_body=True, parse_query=True)
    extracted_data = extractor(request)
    assert await extracted_data.get("body") == await request.json()  # type: ignore[misc]
    assert extracted_data.get("content_type") == request.content_type
    assert extracted_data.get("headers") == dict(request.headers)
    assert extracted_data.get("headers") == dict(request.headers)
    assert extracted_data.get("path") == request.scope["path"]
    assert extracted_data.get("path") == request.scope["path"]
    assert extracted_data.get("path_params") == request.scope["path_params"]
    assert extracted_data.get("query") == request.query_params.dict()
    assert extracted_data.get("scheme") == request.scope["scheme"]


def test_parse_query() -> None:
    request = factory.post(
        path="/a/b/c",
        query_params={"first": ["1", "2", "3"], "second": ["jeronimo"]},
    )
    parsed_extracted_data = ConnectionDataExtractor(parse_query=True)(request)
    unparsed_extracted_data = ConnectionDataExtractor()(request)
    assert parsed_extracted_data.get("query") == request.query_params.dict()
    assert unparsed_extracted_data.get("query") == request.scope["query_string"]
    # Close to avoid warnings about un-awaited coroutines.
    parsed_extracted_data.get("body").close()  # type: ignore[union-attr]
    unparsed_extracted_data.get("body").close()  # type: ignore[union-attr]


async def test_parse_json_data() -> None:
    request = factory.post(path="/a/b/c", data={"hello": "world"})
    assert await ConnectionDataExtractor(parse_body=True)(request).get("body") == await request.json()  # type: ignore[misc]
    assert await ConnectionDataExtractor()(request).get("body") == await request.body()  # type: ignore[misc]


async def test_parse_form_data() -> None:
    request = factory.post(path="/a/b/c", data={"file": b"123"}, request_media_type=RequestEncodingType.MULTI_PART)
    assert await ConnectionDataExtractor(parse_body=True)(request).get("body") == dict(await request.form())  # type: ignore[misc]


async def test_parse_url_encoded() -> None:
    request = factory.post(path="/a/b/c", data={"key": "123"}, request_media_type=RequestEncodingType.URL_ENCODED)
    assert await ConnectionDataExtractor(parse_body=True)(request).get("body") == dict(await request.form())  # type: ignore[misc]


@pytest.mark.parametrize("req", [factory.get(headers={"Special": "123"}), factory.get(headers={"special": "123"})])
def test_request_extraction_header_obfuscation(req: Request[Any, Any, Any]) -> None:
    extractor = ConnectionDataExtractor(obfuscate_headers={"special"})
    extracted_data = extractor(req)
    assert extracted_data.get("headers") == {"special": "*****"}
    # Close to avoid warnings about un-awaited coroutines.
    extracted_data.get("body").close()  # type: ignore[union-attr]


@pytest.mark.parametrize(
    "req, key",
    [
        (factory.get(cookies=[Cookie(key="special")]), "special"),
        (factory.get(cookies=[Cookie(key="Special")]), "Special"),
    ],
)
def test_request_extraction_cookie_obfuscation(req: Request[Any, Any, Any], key: str) -> None:
    extractor = ConnectionDataExtractor(obfuscate_cookies={"special"})
    extracted_data = extractor(req)
    assert extracted_data.get("cookies") == {"Path": "/", "SameSite": "lax", key: "*****"}
    # Close to avoid warnings about un-awaited coroutines.
    extracted_data.get("body").close()  # type: ignore[union-attr]


async def test_response_data_extractor() -> None:
    headers = {"common": "abc", "special": "123", "content-type": "application/json"}
    cookies = [Cookie(key="regular"), Cookie(key="auth")]
    response = ASGIResponse(body=b'{"hello":"world"}', cookies=cookies, headers=headers)
    extractor = ResponseDataExtractor()
    messages: List[Any] = []

    async def send(message: "Any") -> None:
        messages.append(message)

    await response({}, empty_receive, send)  # type: ignore[arg-type]

    assert len(messages) == 2
    extracted_data = extractor(messages)  # type: ignore[arg-type]
    assert extracted_data.get("status_code") == HTTP_200_OK
    assert extracted_data.get("body") == b'{"hello":"world"}'
    assert extracted_data.get("headers") == {**headers, "content-length": "17"}
    assert extracted_data.get("cookies") == {"Path": "/", "SameSite": "lax", "auth": "", "regular": ""}


async def test_request_data_extractor_skip_keys() -> None:
    req = factory.get()
    extractor = ConnectionDataExtractor()
    assert (await extractor.extract(req, {"body"})).keys() == {"body"}


async def test_skip_parse_malformed_body_false_raises(mocker: MockFixture) -> None:
    mocker.patch("litestar.testing.request_factory.Request.json", new=AsyncMock(side_effect=ValueError()))
    req = factory.post(headers={"Content-Type": "application/json"})
    extractor = ConnectionDataExtractor(parse_body=True, skip_parse_malformed_body=False)

    with pytest.raises(ValueError):
        await extractor.extract(req, {"body"})
