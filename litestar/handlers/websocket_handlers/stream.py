from __future__ import annotations

import dataclasses
import functools
import warnings
from collections.abc import AsyncGenerator, Awaitable, Mapping
from typing import TYPE_CHECKING, Any, Callable, cast

import anyio
from msgspec.json import Encoder as JsonEncoder

from litestar.exceptions import ImproperlyConfiguredException, LitestarWarning, WebSocketDisconnect
from litestar.handlers.websocket_handlers.route_handler import WebsocketRouteHandler
from litestar.types import Empty
from litestar.types.builtin_types import NoneType
from litestar.typing import FieldDefinition
from litestar.utils.signature import ParsedSignature

if TYPE_CHECKING:
    from litestar import Litestar, WebSocket
    from litestar.dto import AbstractDTO
    from litestar.routes import BaseRoute
    from litestar.types import Dependencies, EmptyType, ExceptionHandler, Guard, Middleware, TypeEncodersMap
    from litestar.types.asgi_types import WebSocketMode


async def send_websocket_stream(
    socket: WebSocket,
    stream: AsyncGenerator[Any, Any],
    *,
    close: bool = True,
    mode: WebSocketMode = "text",
    send_handler: Callable[[WebSocket, Any], Awaitable[Any]] | None = None,
    listen_for_disconnect: bool = False,
    warn_on_data_discard: bool = True,
) -> None:
    """Stream data to the ``socket`` from an asynchronous generator.

    Example:
        Sending the current time to the connected client every 0.5 seconds:

        .. code-block:: python

            async def stream_current_time() -> AsyncGenerator[str, None]:
                while True:
                    yield str(time.time())
                    await asyncio.sleep(0.5)


            @websocket("/time")
            async def time_handler(socket: WebSocket) -> None:
                await socket.accept()
                await send_websocket_stream(
                    socket,
                    stream_current_time(),
                    listen_for_disconnect=True,
                )


    Args:
        socket: The :class:`~litestar.connection.WebSocket` to send to
        stream: An asynchronous generator yielding data to send
        close: If ``True``, close the socket after the generator is exhausted
        mode: WebSocket mode to use for sending when no ``send_handler`` is specified
        send_handler: Callable to handle the send process. If ``None``, defaults to ``type(socket).send_data``
        listen_for_disconnect: If ``True``, listen for client disconnects in the background. If a client disconnects,
            stop the generator and cancel sending data. Should always be ``True`` unless disconnects are handled
            elsewhere, for example by reading data from the socket concurrently. Should never be set to ``True`` when
            reading data from socket concurrently, as it can lead to data loss
        warn_on_data_discard: If ``True`` and ``listen_for_disconnect=True``, warn if during listening for client
            disconnects, data is received from the socket
    """
    if send_handler is None:
        send_handler = functools.partial(type(socket).send_data, mode=mode)

    async def send_stream() -> None:
        try:
            # client might have disconnected elsewhere, so we stop sending
            while socket.connection_state != "disconnect":
                await send_handler(socket, await stream.__anext__())
        except StopAsyncIteration:
            pass

    if listen_for_disconnect:
        # wrap 'send_stream' and disconnect listener, so they'll cancel the other once
        # one of the finishes
        async def wrapped_stream() -> None:
            await send_stream()
            # stream exhausted, we can stop listening for a disconnect
            tg.cancel_scope.cancel()

        async def disconnect_listener() -> None:
            try:
                # run this in a loop - we might receive other data than disconnects.
                # listen_for_disconnect is explicitly not safe when consuming WS data
                # in other places, so discarding that data here is fine
                while True:
                    await socket.receive_data("text")
                    if warn_on_data_discard:
                        warnings.warn(
                            "received data from websocket while listening for client "
                            "disconnect in a websocket_stream. listen_for_disconnect "
                            "is not safe to use when attempting to receive data from "
                            "the same socket concurrently with a websocket_stream. set "
                            "listen_for_disconnect=False if you're attempting to "
                            "receive data from this socket or set "
                            "warn_on_data_discard=False to disable this warning",
                            stacklevel=2,
                            category=LitestarWarning,
                        )

            except WebSocketDisconnect:
                # client disconnected, we can stop streaming
                tg.cancel_scope.cancel()

        async with anyio.create_task_group() as tg:
            tg.start_soon(wrapped_stream)
            tg.start_soon(disconnect_listener)

    else:
        await send_stream()

    if close and socket.connection_state != "disconnect":
        await socket.close()


def websocket_stream(
    path: str | list[str] | None = None,
    *,
    dependencies: Dependencies | None = None,
    exception_handlers: dict[int | type[Exception], ExceptionHandler] | None = None,
    guards: list[Guard] | None = None,
    middleware: list[Middleware] | None = None,
    name: str | None = None,
    opt: dict[str, Any] | None = None,
    signature_namespace: Mapping[str, Any] | None = None,
    websocket_class: type[WebSocket] | None = None,
    mode: WebSocketMode = "text",
    return_dto: type[AbstractDTO] | None | EmptyType = Empty,
    type_encoders: TypeEncodersMap | None = None,
    listen_for_disconnect: bool = True,
    warn_on_data_discard: bool = True,
    **kwargs: Any,
) -> Callable[[Callable[..., AsyncGenerator[Any, Any]]], WebsocketRouteHandler]:
    """Create a WebSocket handler that accepts a connection and sends data to it from an
    async generator.

    Example:
        Sending the current time to the connected client every 0.5 seconds:

        .. code-block:: python

            @websocket_stream("/time")
            async def send_time() -> AsyncGenerator[str, None]:
                while True:
                    yield str(time.time())
                    await asyncio.sleep(0.5)

    Args:
        path: A path fragment for the route handler function or a sequence of path fragments. If not given defaults
            to ``/``
        dependencies: A string keyed mapping of dependency :class:`Provider <.di.Provide>` instances.
        exception_handlers: A mapping of status codes and/or exception types to handler functions.
        guards: A sequence of :class:`Guard <.types.Guard>` callables.
        middleware: A sequence of :class:`Middleware <.types.Middleware>`.
        name: A string identifying the route handler.
        opt: A string keyed mapping of arbitrary values that can be accessed in :class:`Guards <.types.Guard>` or
            wherever you have access to :class:`Request <.connection.Request>` or
            :class:`ASGI Scope <.types.Scope>`.
        signature_namespace: A mapping of names to types for use in forward reference resolution during signature modelling.
        websocket_class: A custom subclass of :class:`WebSocket <.connection.WebSocket>` to be used as route handler's
            default websocket class.
        mode: WebSocket mode used for sending
        return_dto: :class:`AbstractDTO <.dto.base_dto.AbstractDTO>` to use for serializing outbound response data.
        type_encoders: A mapping of types to callables that transform them into types supported for serialization.
        listen_for_disconnect: If ``True``, listen for client disconnects in the background. If a client disconnects,
            stop the generator and cancel sending data. Should always be ``True`` unless disconnects are handled
            elsewhere, for example by reading data from the socket concurrently. Should never be set to ``True`` when
            reading data from socket concurrently, as it can lead to data loss
        warn_on_data_discard: If ``True`` and ``listen_for_disconnect=True``, warn if during listening for client
            disconnects, data is received from the socket
        **kwargs: Any additional kwarg - will be set in the opt dictionary.
    """

    def decorator(fn: Callable[..., AsyncGenerator[Any, Any]]) -> WebsocketRouteHandler:
        return WebSocketStreamHandler(
            fn=fn,  # type: ignore[arg-type]
            path=path,
            dependencies=dependencies,
            exception_handlers=exception_handlers,
            guard=guards,
            middleware=middleware,
            name=name,
            opt=opt,
            signature_namespace=signature_namespace,
            websocket_class=websocket_class,
            return_dto=return_dto,
            type_encoders=type_encoders,
            stream_options=_WebSocketStreamOptions(
                generator_fn=fn,
                send_mode=mode,
                listen_for_disconnect=listen_for_disconnect,
                warn_on_data_discard=warn_on_data_discard,
            ),
            **kwargs,
        )

    return decorator


class WebSocketStreamHandler(WebsocketRouteHandler):
    __slots__ = ("_ws_stream_options",)
    _ws_stream_options: _WebSocketStreamOptions

    def on_registration(self, route: BaseRoute, app: Litestar) -> None:
        self._ws_stream_options = self.opt["stream_options"]

        parsed_handler_signature = parsed_stream_fn_signature = ParsedSignature.from_fn(
            self.fn, self.signature_namespace
        )

        if not parsed_stream_fn_signature.return_type.is_subclass_of(AsyncGenerator):
            raise ImproperlyConfiguredException(
                f"Route handler {self}: 'websocket_stream' handlers must return an "
                f"'AsyncGenerator', not {type(parsed_stream_fn_signature.return_type.raw)!r}"
            )

        # important not to use 'self._ws_stream_options.generator_fn' here; This would
        # break in cases the decorator has been used inside a controller, as it would
        # be a reference to the unbound method. The bound method is patched in later
        # after the controller has been initialized. This is a workaround that should
        # go away with v3.0's static handlers
        stream_fn = cast(Callable[..., AsyncGenerator[Any, Any]], self.fn)

        # construct a fake signature for the kwargs modelling, using the generator
        # function passed to the handler as a base, to include all the dependencies,
        # params, injection kwargs, etc. + 'socket', so DI works properly, but the
        # signature looks to kwargs/signature modelling like a plain '@websocket'
        # handler that returns 'None'
        parsed_handler_signature = dataclasses.replace(
            parsed_handler_signature, return_type=FieldDefinition.from_annotation(NoneType)
        )
        receives_socket_parameter = "socket" in parsed_stream_fn_signature.parameters

        if not receives_socket_parameter:
            parsed_handler_signature = dataclasses.replace(
                parsed_handler_signature,
                parameters={
                    **parsed_handler_signature.parameters,
                    "socket": FieldDefinition.from_annotation("WebSocket", name="socket"),
                },
            )

        self._parsed_fn_signature = parsed_handler_signature
        self._parsed_return_field = parsed_stream_fn_signature.return_type.inner_types[0]

        json_encoder = JsonEncoder(enc_hook=self.default_serializer)
        self._dto = self._resolve_data_dto(app=app)
        self._return_dto = return_dto = self._resolve_return_dto(app=app, data_dto=self._dto)

        # make sure the closure doesn't capture self._ws_stream / self
        send_mode: WebSocketMode = self._ws_stream_options.send_mode  # pyright: ignore
        listen_for_disconnect = self._ws_stream_options.listen_for_disconnect
        warn_on_data_discard = self._ws_stream_options.warn_on_data_discard

        async def send_handler(socket: WebSocket, data: Any) -> None:
            if isinstance(data, (str, bytes)):
                await socket.send_data(data=data, mode=send_mode)
                return

            if return_dto:
                encoded_data = return_dto(socket).data_to_encodable_type(data)
                data = json_encoder.encode(encoded_data)
                await socket.send_data(data=data, mode=send_mode)
                return

            data = json_encoder.encode(data)
            await socket.send_data(data=data, mode=send_mode)

        @functools.wraps(stream_fn)
        async def handler_fn(*args: Any, socket: WebSocket, **kw: Any) -> None:
            if receives_socket_parameter:
                kw["socket"] = socket

            await send_websocket_stream(
                socket=socket,
                stream=stream_fn(*args, **kw),
                mode=send_mode,
                close=True,
                listen_for_disconnect=listen_for_disconnect,
                warn_on_data_discard=warn_on_data_discard,
                send_handler=send_handler,
            )

        self.fn = handler_fn  # pyright: ignore

        super().on_registration(route, app)


class _WebSocketStreamOptions:
    def __init__(
        self,
        generator_fn: Callable[..., AsyncGenerator[Any, Any]],
        listen_for_disconnect: bool,
        warn_on_data_discard: bool,
        send_mode: WebSocketMode,
    ) -> None:
        self.generator_fn = generator_fn
        self.listen_for_disconnect = listen_for_disconnect
        self.warn_on_data_discard = warn_on_data_discard
        self.send_mode = send_mode
