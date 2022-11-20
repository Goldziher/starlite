from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from anyio import CancelScope, create_task_group
from orjson import OPT_OMIT_MICROSECONDS, OPT_SERIALIZE_NUMPY, dumps

from starlite.constants import DEFAULT_CHUNK_SIZE
from starlite.datastructures import Cookie, ETag
from starlite.enums import MediaType, OpenAPIMediaType
from starlite.exceptions import ImproperlyConfiguredException
from starlite.status_codes import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_304_NOT_MODIFIED,
)
from starlite.utils.helpers import get_enum_string_value
from starlite.utils.serialization import default_serializer

if TYPE_CHECKING:

    from starlite.datastructures import BackgroundTask, BackgroundTasks
    from starlite.types import (
        HTTPResponseBodyEvent,
        HTTPResponseStartEvent,
        Receive,
        ResponseCookies,
        Scope,
        Send,
    )

T = TypeVar("T")


class Response(Generic[T]):
    """Base Starlite HTTP response class, used as the basis for all other response classes."""

    __slots__ = (
        "background",
        "body",
        "cookies",
        "encoding",
        "headers",
        "is_head_response",
        "is_text_response",
        "media_type",
        "status_allows_body",
        "status_code",
        "stream_chunk_size",
        "raw_headers",
    )

    def __init__(
        self,
        content: T,
        *,
        status_code: int = HTTP_200_OK,
        media_type: Union[MediaType, "OpenAPIMediaType", str] = MediaType.JSON,
        background: Optional[Union["BackgroundTask", "BackgroundTasks"]] = None,
        headers: Optional[Dict[str, Any]] = None,
        cookies: Optional["ResponseCookies"] = None,
        encoding: str = "utf-8",
        is_head_response: bool = False,
        stream_chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        """Initialize the response.

        Args:
            content: A value for the response body that will be rendered into bytes string.
            status_code: An HTTP status code.
            media_type: A value for the response 'Content-Type' header.
            background: A [BackgroundTask][starlite.datastructures.BackgroundTask] instance or
                [BackgroundTasks][starlite.datastructures.BackgroundTasks] to execute after the response is finished.
                Defaults to None.
            headers: A string keyed dictionary of response headers. Header keys are insensitive.
            cookies: A list of [Cookie][starlite.datastructures.Cookie] instances to be set under
                the response 'Set-Cookie' header.
            encoding: The encoding to be used for the response headers.
            is_head_response: Whether the response should send only the headers ("head" request) or also the content.
            stream_chunk_size: The size of chunks to stream. If the response body is smaller than this size, it will
                not be streamed, otherwise it will be split into chunks and streamed.
        """
        self.background = background
        self.cookies = cookies or []
        self.encoding = encoding
        self.headers = headers or {}
        self.is_head_response = is_head_response
        self.media_type = get_enum_string_value(media_type)
        self.stream_chunk_size = stream_chunk_size
        self.status_allows_body = not (
            status_code in {HTTP_204_NO_CONTENT, HTTP_304_NOT_MODIFIED} or status_code < HTTP_200_OK
        )
        self.status_code = status_code

        if not self.status_allows_body or is_head_response:
            if content:
                raise ImproperlyConfiguredException(
                    "response content is not supported for HEAD responses and responses with a status code "
                    "that does not allow content (304, 204, < 200)"
                )
            self.body = b""
        else:
            self.body = content if isinstance(content, bytes) else self.render(content)

        self.headers.setdefault(
            "content-type",
            f"{self.media_type}; charset={self.encoding}" if self.media_type.startswith("text/") else self.media_type,
        )
        self.raw_headers: List[Tuple[bytes, bytes]] = []

    def set_cookie(
        self,
        key: str,
        value: Optional[str] = None,
        max_age: Optional[int] = None,
        expires: Optional[int] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Literal["lax", "strict", "none"] = "lax",
    ) -> None:
        """Ses a cookie on the response.

        Args:
            key: Key for the cookie.
            value: Value for the cookie, if none given defaults to empty string.
            max_age: Maximal age of the cookie before its invalidated.
            expires: Expiration date as unix MS timestamp.
            path: Path fragment that must exist in the request url for the cookie to be valid. Defaults to '/'.
            domain: Domain for which the cookie is valid.
            secure: Https is required for the cookie.
            httponly: Forbids javascript to access the cookie via 'Document.cookie'.
            samesite: Controls whether a cookie is sent with cross-site requests. Defaults to 'lax'.

        Returns:
            None.
        """
        self.cookies.append(
            Cookie(
                domain=domain,
                expires=expires,
                httponly=httponly,
                key=key,
                max_age=max_age,
                path=path,
                samesite=samesite,
                secure=secure,
                value=value,
            )
        )

    def set_header(self, key: str, value: str) -> None:
        """Set a header on the response.

        Args:
            key: Header key.
            value: Header value.

        Returns:
            None.
        """
        self.headers[key] = value

    def set_etag(self, etag: Union[str, "ETag"]) -> None:
        """Set an etag header.

        Args:
            etag: An etag value.

        Returns:
            None
        """
        self.headers["etag"] = etag.to_header() if isinstance(etag, ETag) else etag

    def delete_cookie(
        self,
        key: str,
        path: str = "/",
        domain: Optional[str] = None,
    ) -> None:
        """Delete a cookie.

        Args:
            key: Key of the cookie.
            path: Path of the cookie.
            domain: Domain of the cookie.

        Returns:
            None.
        """
        cookie = Cookie(key=key, path=path, domain=domain, expires=0, max_age=0)
        self.cookies = [c for c in self.cookies if c != cookie]
        self.cookies.append(cookie)

    @staticmethod
    def serializer(value: Any) -> Any:
        """Return a serializer for orjson to handle pydantic models.

        Args:
            value: A value to serialize
        Returns:
            A serialized value
        Raises:
            TypeError: if value is not supported
        """
        return default_serializer(value)

    def render(self, content: Any) -> bytes:
        """Handle the rendering of content T into a bytes string.

        Args:
            content: A value for the response body that will be rendered into bytes string.

        Returns:
            An encoded bytes string
        """
        try:
            if self.media_type.startswith("text/"):
                return content.encode(self.encoding) if content else b""  # type: ignore
            return dumps(content, default=self.serializer, option=OPT_SERIALIZE_NUMPY | OPT_OMIT_MICROSECONDS)
        except (AttributeError, ValueError, TypeError) as e:
            raise ImproperlyConfiguredException("Unable to serialize response content") from e

    @property
    def content_length(self) -> Optional[int]:
        """Content length of the response if applicable.

        Returns:
            The content length of the body (e.g. for use in a "Content-Length" header).
            If the response does not have a body, this value is `None`
        """
        if self.status_allows_body:
            return len(self.body)
        return None

    def encode_headers(self) -> List[Tuple[bytes, bytes]]:
        """Encode the response headers as a list of byte tuples.

        Notes:
            - A 'Content-Length' header will be added if appropriate and not provided by the user.

        Returns:
            A list of tuples containing the headers and cookies of the request in a format ready for ASGI transmission.
        """

        return list(
            chain(
                ((k.lower().encode("latin-1"), str(v).encode("latin-1")) for k, v in self.headers.items()),
                (cookie.to_encoded_header() for cookie in self.cookies),
                self.raw_headers,
            )
        )

    async def after_response(self) -> None:
        """Execute after the response is sent.

        Returns:
            None
        """
        if self.background is not None:
            await self.background()

    async def start_response(self, send: "Send") -> None:
        """Emit the start event of the response. This event includes the headers and status codes.

        Args:
            send: The ASGI send function.

        Returns:
            None
        """

        encoded_headers = self.encode_headers()

        content_length = self.content_length
        if "content-length" not in self.headers and content_length:
            encoded_headers.append((b"content-length", str(content_length).encode("latin-1")))

        event: "HTTPResponseStartEvent" = {
            "type": "http.response.start",
            "status": self.status_code,
            "headers": encoded_headers,
        }

        await send(event)

    async def _listen_for_disconnect(self, cancel_scope: "CancelScope", receive: "Receive") -> None:
        """Listen for a cancellation message, and if received - call cancel on the cancel scope.

        Args:
            cancel_scope: A task group cancel scope instance.
            receive: The ASGI receive function.

        Returns:
            None
        """
        if not cancel_scope.cancel_called:
            message = await receive()
            if message["type"] == "http.disconnect":
                # despite the IDE warning, this is not a coroutine because anyio 3+ changed this.
                # therefore make sure not to await this.
                cancel_scope.cancel()
            else:
                await self._listen_for_disconnect(cancel_scope=cancel_scope, receive=receive)

    def create_stream(self, send: "Send") -> Callable[[], Coroutine[None, None, None]]:
        """Create a function that streams the response body.

        Args:
            send: The ASGI Send function.

        Returns:
            A stream function
        """

        async def stream() -> None:
            for chunk in iter(
                self.body[i : i + self.stream_chunk_size] for i in range(0, len(self.body), self.stream_chunk_size)
            ):
                stream_event: "HTTPResponseBodyEvent" = {
                    "type": "http.response.body",
                    "body": chunk,
                    "more_body": True,
                }
                await send(stream_event)

            terminus_event: "HTTPResponseBodyEvent" = {"type": "http.response.body", "body": b"", "more_body": False}
            await send(terminus_event)

        return stream

    async def send_body(self, send: "Send", receive: "Receive") -> None:
        """Emit the response body.

        Args:
            send: The ASGI send function.
            receive: The ASGI receive function.

        Notes:
            - Response subclasses should customize this method if there is a need to customize sending data.

        Returns:
            None
        """
        if self.content_length and self.content_length >= self.stream_chunk_size:
            async with create_task_group() as task_group:
                task_group.start_soon(self.create_stream(send=send))
                await self._listen_for_disconnect(cancel_scope=task_group.cancel_scope, receive=receive)
        else:
            event: "HTTPResponseBodyEvent" = {"type": "http.response.body", "body": self.body, "more_body": False}
            await send(event)

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        """ASGI callable of the `Response`.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None
        """
        await self.start_response(send=send)

        if self.is_head_response:
            event: "HTTPResponseBodyEvent" = {"type": "http.response.body", "body": b"", "more_body": False}
            await send(event)
        else:
            await self.send_body(send=send, receive=receive)

        await self.after_response()
