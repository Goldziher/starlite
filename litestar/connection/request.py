from __future__ import annotations

import math
import warnings
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final, Generic, cast

import anyio

from litestar._multipart import parse_content_header, parse_multipart_form
from litestar._parsers import parse_url_encoded_form_data
from litestar.connection.base import (
    ASGIConnection,
    AuthT,
    StateT,
    UserT,
    empty_receive,
    empty_send,
)
from litestar.datastructures.headers import Accept
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.enums import ASGIExtension, RequestEncodingType
from litestar.exceptions import (
    ClientException,
    InternalServerException,
    LitestarException,
    LitestarWarning,
)
from litestar.exceptions.base_exceptions import ClientDisconnect
from litestar.exceptions.http_exceptions import RequestEntityTooLarge
from litestar.serialization import decode_json, decode_msgpack
from litestar.types import Empty, HTTPReceiveMessage

__all__ = ("Request",)


if TYPE_CHECKING:
    from litestar.handlers.http_handlers import HTTPRouteHandler  # noqa: F401
    from litestar.types.asgi_types import HTTPScope, Method, Receive, Scope, Send
    from litestar.types.empty import EmptyType


SERVER_PUSH_HEADERS = {
    "accept",
    "accept-encoding",
    "accept-language",
    "cache-control",
    "user-agent",
}


METHODS_WITHOUT_BODY: Final = frozenset(["GET", "HEAD", "DELETE", "TRACE"])


class Request(Generic[UserT, AuthT, StateT], ASGIConnection["HTTPRouteHandler", UserT, AuthT, StateT]):
    """The Litestar Request class."""

    __slots__ = (
        "_accept",
        "_body",
        "_content_length",
        "_content_type",
        "_expect_body",
        "_form",
        "_json",
        "_msgpack",
        "_stream_consumed",
        "is_connected",
        "supports_push_promise",
    )

    scope: HTTPScope  # pyright: ignore
    """The ASGI scope attached to the connection."""
    receive: Receive
    """The ASGI receive function."""
    send: Send
    """The ASGI send function."""

    def __init__(self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send) -> None:
        """Initialize ``Request``.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.
        """
        super().__init__(scope, receive, send)
        self.is_connected: bool = True
        self._body: bytes | EmptyType = self._connection_state.body
        self._form: FormMultiDict | EmptyType = Empty
        self._json: Any = Empty
        self._msgpack: Any = Empty
        self._content_type: tuple[str, dict[str, str]] | EmptyType = Empty
        self._accept: Accept | EmptyType = Empty
        self._content_length: int | None | EmptyType = Empty
        self.supports_push_promise = ASGIExtension.SERVER_PUSH in self._server_extensions
        self._stream_consumed = anyio.Event()
        self._expect_body = self.method not in METHODS_WITHOUT_BODY

    @property
    def method(self) -> Method:
        """Return the request method.

        Returns:
            The request :class:`Method <litestar.types.Method>`
        """
        return self.scope["method"]

    @property
    def content_type(self) -> tuple[str, dict[str, str]]:
        """Parse the request's 'Content-Type' header, returning the header value and any options as a dictionary.

        Returns:
            A tuple with the parsed value and a dictionary containing any options send in it.
        """
        if self._content_type is Empty:
            if (content_type := self._connection_state.content_type) is not Empty:
                self._content_type = content_type
            else:
                self._content_type = self._connection_state.content_type = parse_content_header(
                    self.headers.get("Content-Type", "")
                )
        return self._content_type

    @property
    def accept(self) -> Accept:
        """Parse the request's 'Accept' header, returning an :class:`Accept <litestar.datastructures.headers.Accept>` instance.

        Returns:
            An :class:`Accept <litestar.datastructures.headers.Accept>` instance, representing the list of acceptable media types.
        """
        if self._accept is Empty:
            if (accept := self._connection_state.accept) is not Empty:
                self._accept = accept
            else:
                self._accept = self._connection_state.accept = Accept(self.headers.get("Accept", "*/*"))
        return self._accept

    async def json(self) -> Any:
        """Retrieve the json request body from the request.

        Returns:
            An arbitrary value
        """
        if self._json is Empty:
            if (json_ := self._connection_state.json) is not Empty:
                self._json = json_
            else:
                body = await self.body()
                self._json = self._connection_state.json = decode_json(
                    body or b"null", type_decoders=self.route_handler.resolve_type_decoders()
                )
        return self._json

    async def msgpack(self) -> Any:
        """Retrieve the MessagePack request body from the request.

        Returns:
            An arbitrary value
        """
        if self._msgpack is Empty:
            if (msgpack := self._connection_state.msgpack) is not Empty:
                self._msgpack = msgpack
            else:
                body = await self.body()
                self._msgpack = self._connection_state.msgpack = decode_msgpack(
                    body or b"\xc0", type_decoders=self.route_handler.resolve_type_decoders()
                )
        return self._msgpack

    @property
    def content_length(self) -> int | None:
        cached_content_length = self._content_length
        if cached_content_length is not Empty:
            return cached_content_length

        content_length_header = self.headers.get("content-length")
        try:
            content_length = self._content_length = (
                int(content_length_header) if content_length_header is not None else None
            )
        except ValueError:
            raise ClientException(f"Invalid content-length: {content_length_header!r}") from None
        return content_length

    async def _listen_for_disconnect(self) -> None:
        # we consider these methods empty and consume their - empty - body, since
        # handlers are unlikely to do this, in order to trigger the next phase and
        # start listening for 'http.disconnect'.
        if self.method in METHODS_WITHOUT_BODY:
            body = await self.body()
            if body and not self._expect_body:
                warnings.warn(
                    f"Discarding unexpected request body for '{self.method} {self.url.path}' "
                    "received while listening for disconnect",
                    category=LitestarWarning,
                    stacklevel=2,
                )

        await self._stream_consumed.wait()

        message = await self.receive()
        if message["type"] == "http.disconnect":
            raise ClientDisconnect

        raise InternalServerException(
            f"Received unexpected {message['type']!r} message while listening for 'http.disconnect'"
        )

    async def stream(self) -> AsyncGenerator[bytes, None]:
        """Return an async generator that streams chunks of bytes.

        Returns:
            An async generator.

        Raises:
            RuntimeError: if the stream is already consumed
        """
        if self._body is Empty:
            if not self.is_connected:
                raise InternalServerException("stream consumed")

            announced_content_length = self.content_length
            # setting this to 'math.inf' as a micro-optimisation; Comparing against a
            # float is slightly faster than checking if a value is 'None' and then
            # comparing it to an int. since we expect a limit to be set most of the
            # time, this is a bit more efficient
            max_content_length = self.route_handler.resolve_request_max_body_size() or math.inf

            # if the 'content-length' header is set, and exceeds the limit, we can bail
            # out early before reading anything
            if announced_content_length is not None and announced_content_length > max_content_length:
                raise RequestEntityTooLarge

            total_bytes_streamed: int = 0
            while event := cast("HTTPReceiveMessage", await self.receive()):
                if event["type"] == "http.request":
                    body = event["body"]
                    if body:
                        total_bytes_streamed += len(body)

                        # if a 'content-length' header was set, check if we have
                        # received more bytes than specified. in most cases this should
                        # be caught before it hits the application layer and an ASGI
                        # server (e.g. uvicorn) will not allow this, but since it's not
                        # forbidden according to the HTTP or ASGI spec, we err on the
                        # side of caution and still perform this check.
                        #
                        # uvicorn documented behaviour for this case:
                        # https://github.com/encode/uvicorn/blob/fe3910083e3990695bc19c2ef671dd447262ae18/docs/server-behavior.md?plain=1#L11
                        if announced_content_length:
                            if total_bytes_streamed > announced_content_length:
                                raise ClientException("Malformed request")

                        # we don't have a 'content-length' header, likely a chunked
                        # transfer. we don't really care and simply check if we have
                        # received more bytes than allowed
                        elif total_bytes_streamed > max_content_length:
                            raise RequestEntityTooLarge

                        yield body

                    if not event.get("more_body", False):
                        self._stream_consumed.set()
                        break

                elif event["type"] == "http.disconnect":
                    raise ClientDisconnect()

            self.is_connected = False
            yield b""

        else:
            yield self._body
            yield b""
            return

    async def body(self) -> bytes:
        """Return the body of the request.

        Returns:
            A byte-string representing the body of the request.
        """
        if self._body is Empty:
            if (body := self._connection_state.body) is not Empty:
                self._body = body
            else:
                self._body = self._connection_state.body = b"".join([c async for c in self.stream()])
        return self._body

    async def form(self) -> FormMultiDict:
        """Retrieve form data from the request. If the request is either a 'multipart/form-data' or an
        'application/x-www-form- urlencoded', return a FormMultiDict instance populated with the values sent in the
        request, otherwise, an empty instance.

        Returns:
            A FormMultiDict instance
        """
        if self._form is Empty:
            if (form_data := self._connection_state.form) is Empty:
                content_type, options = self.content_type
                if content_type == RequestEncodingType.MULTI_PART:
                    form_data = await parse_multipart_form(
                        stream=self.stream(),
                        boundary=options.get("boundary", "").encode(),
                        multipart_form_part_limit=self.app.multipart_form_part_limit,
                    )
                elif content_type == RequestEncodingType.URL_ENCODED:
                    form_data = parse_url_encoded_form_data(  # type: ignore[assignment]
                        await self.body(),
                    )
                else:
                    form_data = {}

                self._connection_state.form = form_data  # pyright: ignore

            self._form = FormMultiDict.from_form_data(cast("dict[str, Any]", form_data))

        return self._form

    async def send_push_promise(self, path: str, raise_if_unavailable: bool = False) -> None:
        """Send a push promise.

        This method requires the `http.response.push` extension to be sent from the ASGI server.

        Args:
            path: Path to send the promise to.
            raise_if_unavailable: Raise an exception if server push is not supported by
                the server

        Returns:
            None
        """
        if not self.supports_push_promise:
            if raise_if_unavailable:
                raise LitestarException("Attempted to send a push promise but the server does not support it")

            warnings.warn(
                "Attempted to send a push promise but the server does not support it. In a future version, this will "
                "raise an exception. To enable this behaviour in the current version, set raise_if_unavailable=True. "
                "To prevent this behaviour, make sure that the server you are using supports the 'http.response.push' "
                "ASGI extension, or check this dynamically via "
                ":attr:`~litestar.connection.Request.supports_push_promise`",
                stacklevel=2,
                category=LitestarWarning,
            )

            return

        raw_headers = [
            (header_name.encode("latin-1"), value.encode("latin-1"))
            for header_name in (self.headers.keys() & SERVER_PUSH_HEADERS)
            for value in self.headers.getall(header_name, [])
        ]
        await self.send({"type": "http.response.push", "path": path, "headers": raw_headers})
