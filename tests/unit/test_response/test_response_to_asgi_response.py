from __future__ import annotations

from collections.abc import Generator, Iterator
from inspect import iscoroutine
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Any, cast

import pytest
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.responses import Response as StarletteResponse

from litestar import Litestar, MediaType, Request, Response, get
from litestar.background_tasks import BackgroundTask
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import Cookie, ResponseHeader
from litestar.response import ServerSentEvent
from litestar.response.base import ASGIResponse
from litestar.response.file import ASGIFileResponse, File
from litestar.response.redirect import Redirect
from litestar.response.streaming import ASGIStreamingResponse, Stream
from litestar.response.template import Template
from litestar.status_codes import HTTP_200_OK, HTTP_308_PERMANENT_REDIRECT
from litestar.template.config import TemplateConfig
from litestar.testing import RequestFactory, create_test_client
from litestar.types import StreamType
from litestar.utils import AsyncIteratorWrapper

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from litestar.routes import HTTPRoute


def my_generator() -> Generator[str, None, None]:
    for count in range(1, 11):
        yield str(count)
    return


async def my_async_generator() -> AsyncGenerator[str, None]:
    for count in range(1, 11):
        yield str(count)
    return


class MySyncIterator:
    def __init__(self) -> None:
        self.delay = 0.01
        self.i = 1
        self.to = 10

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        i = self.i
        if i > self.to:
            raise StopIteration
        self.i += 1
        if i:
            sleep(self.delay)
        return str(i)


class MyAsyncIterator(AsyncIteratorWrapper[str]):
    def __init__(self) -> None:
        super().__init__(iterator=MySyncIterator())


async def test_to_response_returning_litestar_response() -> None:
    @get(path="/test")
    def handler() -> Response:
        return Response(media_type=MediaType.TEXT, content="ok")

    with create_test_client(handler) as client:
        http_route: HTTPRoute = client.app.routes[0]
        route_handler = http_route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), request=RequestFactory().get())
        assert isinstance(response, ASGIResponse)


@pytest.mark.parametrize(
    "expected_response",
    [
        StarletteResponse(status_code=HTTP_200_OK, content=b"abc"),
        PlainTextResponse(content="abc"),
        HTMLResponse(content="<div><span/></div"),
        JSONResponse(status_code=HTTP_200_OK, content={}),
    ],
)
async def test_to_response_returning_starlette_response(
    expected_response: StarletteResponse, anyio_backend: str
) -> None:
    @get(path="/test")
    def handler() -> StarletteResponse:
        return expected_response

    with create_test_client(handler) as client:
        http_route: HTTPRoute = client.app.routes[0]
        route_handler = http_route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), request=RequestFactory().get())
        assert isinstance(response, StarletteResponse)
        assert response is expected_response


async def test_to_response_returning_redirect_response(anyio_backend: str) -> None:
    background_task = BackgroundTask(lambda: "")

    @get(
        path="/test",
        status_code=301,
        response_headers=[ResponseHeader(name="local-header", value="123")],
        response_cookies=[Cookie(key="redirect-cookie", value="aaa"), Cookie(key="general-cookie", value="xxx")],
    )
    def handler() -> Redirect:
        return Redirect(
            path="/somewhere-else",
            headers={"response-header": "abc"},
            cookies=[Cookie(key="redirect-cookie", value="xyz")],
            background=background_task,
        )

    with create_test_client(handler) as client:
        route: HTTPRoute = client.app.routes[0]
        route_handler = route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), request=RequestFactory().get())
        encoded_headers = response.encode_headers()  # type: ignore[attr-defined]

        assert isinstance(response, ASGIResponse)
        assert (b"location", b"/somewhere-else") in encoded_headers
        assert (b"local-header", b"123") in encoded_headers
        assert (b"response-header", b"abc") in encoded_headers
        assert (b"set-cookie", b"general-cookie=xxx; Path=/; SameSite=lax") in encoded_headers
        assert (b"set-cookie", b"redirect-cookie=xyz; Path=/; SameSite=lax") in encoded_headers
        assert response.background == background_task


def test_to_response_returning_redirect_response_from_redirect() -> None:
    @get(path="/proxy")
    def proxy_handler() -> dict:
        return {"message": "redirected by before request hook"}

    def before_request_hook_handler(_: Request) -> Redirect:
        return Redirect(path="/proxy", status_code=HTTP_308_PERMANENT_REDIRECT)

    @get(path="/test", before_request=before_request_hook_handler)
    def redirect_handler() -> None:
        raise AssertionError("this endpoint should not be reached")

    with create_test_client(route_handlers=[redirect_handler, proxy_handler]) as client:
        response = client.get("/test")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"message": "redirected by before request hook"}


async def test_to_response_returning_file_response(anyio_backend: str) -> None:
    current_file_path = Path(__file__).resolve()
    filename = Path(__file__).name
    background_task = BackgroundTask(lambda: "")

    @get(
        path="/test",
        response_headers=[ResponseHeader(name="local-header", value="123")],
        response_cookies=[Cookie(key="redirect-cookie", value="aaa"), Cookie(key="general-cookie", value="xxx")],
    )
    def handler() -> File:
        return File(
            path=current_file_path,
            filename=filename,
            headers={"response-header": "abc"},
            cookies=[Cookie(key="file-cookie", value="xyz")],
            background=background_task,
        )

    with create_test_client(handler) as client:
        route: HTTPRoute = client.app.routes[0]
        route_handler = route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), request=RequestFactory().get())
        assert isinstance(response, ASGIFileResponse)
        assert response.file_info
        if iscoroutine(response.file_info):
            await response.file_info

        encoded_headers = response.encode_headers()
        assert (b"local-header", b"123") in encoded_headers
        assert (b"response-header", b"abc") in encoded_headers
        assert (b"set-cookie", b"file-cookie=xyz; Path=/; SameSite=lax") in encoded_headers
        assert (b"set-cookie", b"general-cookie=xxx; Path=/; SameSite=lax") in encoded_headers
        assert (b"set-cookie", b"redirect-cookie=aaa; Path=/; SameSite=lax") in encoded_headers
        assert response.background == background_task


@pytest.mark.parametrize(
    "iterator, should_raise",
    [
        [my_generator(), False],
        [my_async_generator(), False],
        [MySyncIterator(), False],
        [MyAsyncIterator(), False],
        [my_generator, False],
        [my_async_generator, False],
        [MyAsyncIterator, False],
        [MySyncIterator, False],
        [[1, 2, 3, 4], False],
        ["abc", False],
        [b"abc", False],
        [{"key": 1}, False],
        [[{"key": 1}], False],
        [1, True],
        [None, True],
    ],
)
async def test_to_response_streaming_response(iterator: Any, should_raise: bool, anyio_backend: str) -> None:
    background_task = BackgroundTask(lambda: "")

    @get(
        path="/test",
        response_headers=[ResponseHeader(name="local-header", value="123")],
        response_cookies=[Cookie(key="redirect-cookie", value="aaa"), Cookie(key="general-cookie", value="xxx")],
    )
    def handler() -> Stream:
        return Stream(
            iterator,
            headers={"response-header": "abc"},
            cookies=[Cookie(key="streaming-cookie", value="xyz")],
            background=background_task,
        )

    with create_test_client(handler) as client:
        route: HTTPRoute = client.app.routes[0]
        route_handler = route.route_handlers[0]
        if should_raise:
            with pytest.raises(TypeError):
                await route_handler.to_response(data=route_handler.fn(), request=RequestFactory().get())
        else:
            response = await route_handler.to_response(data=route_handler.fn(), request=RequestFactory().get())
            assert isinstance(response, ASGIStreamingResponse)
            encoded_headers = response.encode_headers()
            assert (b"local-header", b"123") in encoded_headers
            assert (b"response-header", b"abc") in encoded_headers
            assert (b"set-cookie", b"general-cookie=xxx; Path=/; SameSite=lax") in encoded_headers
            assert (b"set-cookie", b"redirect-cookie=aaa; Path=/; SameSite=lax") in encoded_headers
            assert (b"set-cookie", b"streaming-cookie=xyz; Path=/; SameSite=lax") in encoded_headers
            assert response.background == background_task


async def test_to_response_template_response(anyio_backend: str, tmp_path: Path) -> None:
    background_task = BackgroundTask(lambda: "")

    p = tmp_path / "test.template"
    p.write_text("<h1>hello world</h1>")

    @get(
        path="/test",
        response_headers=[ResponseHeader(name="local-header", value="123")],
        response_cookies=[Cookie(key="redirect-cookie", value="aaa"), Cookie(key="general-cookie", value="xxx")],
    )
    def handler() -> Template:
        return Template(
            template_name="test.template",
            context={},
            headers={"response-header": "abc"},
            cookies=[Cookie(key="template-cookie", value="xyz")],
            background=background_task,
        )

    app = Litestar(
        route_handlers=[],
        template_config=TemplateConfig(
            engine=JinjaTemplateEngine,
            directory=tmp_path,
        ),
    )

    with create_test_client(
        handler, template_config=TemplateConfig(engine=JinjaTemplateEngine, directory=tmp_path)
    ) as client:
        route: HTTPRoute = client.app.routes[0]
        route_handler = route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), request=RequestFactory(app=app).get())
        assert isinstance(response, ASGIResponse)
        encoded_headers = response.encode_headers()

        assert (b"local-header", b"123") in encoded_headers
        assert (b"response-header", b"abc") in encoded_headers
        assert (b"set-cookie", b"general-cookie=xxx; Path=/; SameSite=lax") in encoded_headers
        assert (b"set-cookie", b"template-cookie=xyz; Path=/; SameSite=lax") in encoded_headers
        assert response.background == background_task


@pytest.mark.parametrize(
    "content",
    [
        my_generator(),
        my_async_generator(),
        MySyncIterator(),
        MyAsyncIterator(),
        my_generator,
        my_async_generator,
        MyAsyncIterator,
        MySyncIterator,
        [1, 2, 3, 4],
        "abc",
        b"abc",
        {"key": 1},
        [{"key": 1}],
    ],
)
async def test_to_response_sse_events(content: str | bytes | StreamType[str | bytes]) -> None:
    background_task = BackgroundTask(lambda: "")

    @get(
        path="/test",
    )
    def handler() -> ServerSentEvent:
        return ServerSentEvent(
            content=content,
            headers={"response-header": "abc"},
            cookies=[Cookie(key="streaming-cookie", value="xyz")],
            background=background_task,
            comment_message="my comment message\r\nwith some\nmixed line breaks",
            event_id="123",
            event_type="special",
        )

    with create_test_client(handler) as client:
        route: HTTPRoute = client.app.routes[0]
        route_handler = route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), request=RequestFactory().get())
        encoded_headers = response.encode_headers()  # type: ignore[attr-defined]

        assert isinstance(response, ASGIStreamingResponse)
        assert ((b"cache-control", b"no-cache")) in encoded_headers
        assert (b"x-accel-buffering", b"no") in encoded_headers
        assert (b"connection", b"keep-alive") in encoded_headers
        assert (b"content-type", b"text/event-stream; charset=utf-8") in encoded_headers
        assert (b"response-header", b"abc") in encoded_headers
        assert (b"set-cookie", b"streaming-cookie=xyz; Path=/; SameSite=lax") in encoded_headers
        assert response.background == background_task


@pytest.mark.parametrize(
    "content",
    [
        my_generator(),
        my_async_generator(),
        my_generator,
        my_async_generator,
        MySyncIterator(),
        MyAsyncIterator(),
        MyAsyncIterator,
        MySyncIterator,
    ],
)
async def test_sse_events_content(content: str | bytes | StreamType[str | bytes]) -> None:
    @get(
        path="/test",
    )
    def handler() -> ServerSentEvent:
        return ServerSentEvent(
            content=content,
            comment_message="my comment message\r\nwith some\nmixed line breaks",
            event_id="123",
            event_type="special",
        )

    events: list[bytes] = []

    with create_test_client(handler) as client:
        route: HTTPRoute = client.app.routes[0]
        route_handler = route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), request=RequestFactory().get())
        assert isinstance(response, ASGIStreamingResponse)
        async for value in response.iterator:
            events.append(cast("bytes", value))

    assert events == [
        b": my comment message\r\n",
        b": with some\r\n",
        b": mixed line breaks\r\n",
        b"id: 123\r\n",
        b"event: special\r\n",
        b"id: 123\r\nevent: special\r\ndata: 1\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 2\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 3\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 4\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 5\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 6\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 7\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 8\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 9\r\n\r\n",
        b"id: 123\r\nevent: special\r\ndata: 10\r\n\r\n",
    ]
