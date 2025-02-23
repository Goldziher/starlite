WebSockets
==========

There are three ways to handle WebSockets in Litestar:

1. The low-level :func:`~litestar.handlers.websocket` route handler, providing basic
   abstractions over the ASGI WebSocket interface
2. :func:`~litestar.handlers.websocket_listener` and :class:`~litestar.handlers.WebsocketListener`\  :
   Reactive, event-driven WebSockets with full serialization and DTO support and support
   for a synchronous interface
3. :func:`~litestar.handlers.websocket_stream` and :func:`~litestar.handlers.send_websocket_stream`\ :
   Proactive, stream oriented WebSockets with full serialization and DTO support


The main difference between the low and high level interfaces is that, dealing with low
level interface requires, setting up a loop and listening for incoming data, handling
exceptions, client disconnects, and parsing incoming and serializing outgoing data.



WebSocket Listeners
--------------------

WebSocket Listeners can be used to interact with a WebSocket in an event-driven manner,
using a callback style interface. They treat a WebSocket handler like any other route
handler: A callable that takes in incoming data in an already pre-processed form and
returns data to be serialized and sent over the connection. The low level details will
be handled behind the curtains.


.. code-block:: python

    from litestar import Litestar
    from litestar.handlers.websocket_handlers import websocket_listener


    @websocket_listener("/")
    async def handler(data: str) -> str:
        return data


    app = Litestar([handler])


This handler will accept connections on ``/``, and wait to receive data. Once a message
has been received, it will be passed into the handler function defined, via the ``data``
parameter. This works like a regular route handler, so it's possible to specify the
type of data which should be received, and it will be converted accordingly.

.. note::
    Contrary to WebSocket route handlers, functions decorated with
    :func:`websocket_listener <.handlers.websocket_listener>` don't have to be
    asynchronous.



Receiving data
++++++++++++++

Data can be received in the listener via the ``data`` parameter. The data passed to this
will be converted / parsed according to the given type annotation and supports
:class:`str`, :class:`bytes`, or arbitrary :class:`dict`\ s / or :class:`list`\ s in the
form of JSON.

.. tab-set::

    .. tab-item:: JSON

        .. literalinclude:: /examples/websockets/receive_json.py
            :language: python


    .. tab-item:: Text

        .. literalinclude:: /examples/websockets/receive_str.py
            :language: python


    .. tab-item:: Bytes

        .. literalinclude:: /examples/websockets/receive_bytes.py
            :language: python


.. important::

    Contrary to route handlers, JSON data will only be parsed but not validated. This
    is a limitation of the current implementation and will change in future versions.


Sending data
+++++++++++++

Sending data is done by simply returning the value to be sent from the handler function.
Similar to receiving data, type annotations configure how the data is being handled.
Values that are not :class:`str` or :class:`bytes` are assumed to be JSON encodable and
will be serialized accordingly before being sent. This serialization is available for
all data types currently supported by Litestar (
:doc:`dataclasses <python:library/dataclasses>`\ , :class:`TypedDict <typing.TypedDict>`,
:class:`NamedTuple <typing.NamedTuple>`,  :class:`msgspec.Struct`, etc.), including
DTOs.


.. tab-set::

    .. tab-item:: Text

        .. literalinclude:: /examples/websockets/sending_str.py
            :language: python

    .. tab-item:: Bytes

        .. literalinclude:: /examples/websockets/sending_bytes.py
            :language: python

    .. tab-item:: Dict as JSON

        .. literalinclude:: /examples/websockets/sending_json_dict.py
            :language: python


    .. tab-item:: Dataclass as JSON

        .. literalinclude:: /examples/websockets/sending_json_dataclass.py
            :language: python


Setting transport modes
+++++++++++++++++++++++


Receive mode
~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Text mode

        ``text`` is the default mode and is appropriate for most messages, including
        structured data such as JSON.

        .. literalinclude:: /examples/websockets/mode_receive_text.py
            :language: python


    .. tab-item:: Binary mode

        .. literalinclude:: /examples/websockets/mode_receive_binary.py
            :language: python


.. important::
    Once configured with a mode, a listener will only listen to socket events of the
    appropriate type. This means if a listener is configured to use ``binary`` mode,
    it will not respond to WebSocket events sending data in the text channel.


Send mode
~~~~~~~~~

.. tab-set::

    .. tab-item:: Text mode

        ``text`` is the default mode and is appropriate for most messages, including
        structured data such as JSON.

        .. literalinclude:: /examples/websockets/mode_send_text.py
            :language: python


    .. tab-item:: Binary mode

        .. literalinclude:: /examples/websockets/mode_send_binary.py
            :language: python




Dependency injection
++++++++++++++++++++

:doc:`dependency-injection` is available and generally works the same as in regular
route handlers:

.. literalinclude:: /examples/websockets/dependency_injection_simple.py
    :language: python


.. important::
    Injected dependencies work on the level of the underlying **route handler**. This
    means they won't be re-evaluated every time the listener function is called.

The following example makes use of :ref:`yield dependencies <yield_dependencies>` and
the fact that dependencies are only evaluated once for every connection; The step after
the ``yield`` will only be executed after the connection has been closed.


.. literalinclude:: /examples/websockets/dependency_injection_yield.py
    :language: python



Interacting with the WebSocket directly
+++++++++++++++++++++++++++++++++++++++

Sometimes access to the socket instance is needed, in which case the
:class:`WebSocket <.connection.WebSocket>` instance can be injected into the handler
function via the ``socket`` argument:

.. literalinclude:: /examples/websockets/socket_access.py
    :language: python


.. important::
    Since WebSockets are inherently asynchronous, to interact with the asynchronous
    methods on :class:`WebSocket <.connection.WebSocket>`, the handler function needs
    to be asynchronous.


Customising connection acceptance
+++++++++++++++++++++++++++++++++

By default, Litestar will accept all incoming connections by awaiting ``WebSocket.accept()`` without arguments.
This behavior can be customized by passing a custom ``connection_accept_handler`` function. Litestar will await this
function to accept the connection.

.. literalinclude:: /examples/websockets/setting_custom_connection_headers.py
    :language: python


Class based WebSocket handling
++++++++++++++++++++++++++++++

In addition to using a simple function as in the examples above, a class based approach
is made possible by extending the
:class:`WebSocketListener <.handlers.WebsocketListener>`. This provides
convenient access to socket events such as connect and disconnect, and can be used to
encapsulate more complex logic.


.. tab-set::

    .. tab-item:: Sync

        .. literalinclude:: /examples/websockets/listener_class_based.py
            :language: python

    .. tab-item:: Async

        .. literalinclude:: /examples/websockets/listener_class_based_async.py
            :language: python


Custom WebSocket
++++++++++++++++

.. versionadded:: 2.7.0

Litestar supports custom ``websocket_class`` instances, which can be used to further configure the default :class:`WebSocket`.
The example below illustrates how to implement a custom WebSocket class for the whole application.

.. dropdown:: Example of a custom websocket at the application level

    .. literalinclude:: /examples/websockets/custom_websocket.py
        :language: python

.. admonition:: Layered architecture

   WebSocket classes are part of Litestar's layered architecture, which means you can
   set a WebSocket class on every layer of the application. If you have set a WebSocket
   class on multiple layers, the layer closest to the route handler will take precedence.

   You can read more about this in the :ref:`usage/applications:layered architecture` section


WebSocket Streams
-----------------

WebSocket streams can be used to proactively push data to a client, using an
asynchronous generator function. Data will be sent via the socket every time the
generator ``yield``\ s, until it is either exhausted or the client disconnects.

.. literalinclude:: /examples/websockets/stream_basic.py
    :language: python
    :caption: Streaming the current time in 0.5 second intervals


Serialization
+++++++++++++

Just like with route handlers, type annotations configure how the data is being handled.
:class:`str` or :class:`bytes` will be sent as-is, while everything else will be encoded
as JSON before being sent. This serialization is available for all data types currently
supported by Litestar (:doc:`dataclasses <python:library/dataclasses>`,
:class:`TypedDict <typing.TypedDict>`, :class:`NamedTuple <typing.NamedTuple>`,
:class:`msgspec.Struct`, etc.), including DTOs.


Dependency Injection
++++++++++++++++++++

Dependency injection is available and works analogous to regular route handlers.

.. important::
    One thing to keep in mind, especially for long-lived streams, is that dependencies
    are scoped to the lifetime of the handler. This means that if for example a
    database connection is acquired in a dependency, it will be held until the generator
    stops. This may not be desirable in all cases, and acquiring resources ad-hoc inside
    the generator itself preferable

    .. literalinclude:: /examples/websockets/stream_di_hog.py
        :language: python
        :caption: Bad: The lock will be held until the client disconnects


    .. literalinclude:: /examples/websockets/stream_di_hog_fix.py
        :language: python
        :caption: Good: The lock will only be acquired when it's needed


Interacting with the WebSocket directly
+++++++++++++++++++++++++++++++++++++++

To interact with the :class:`WebSocket <.connection.WebSocket>` directly, it can be
injected into the generator function via the ``socket`` argument:

.. literalinclude:: /examples/websockets/stream_socket_access.py
    :language: python


Receiving data while streaming
++++++++++++++++++++++++++++++

By default, a stream will listen for a client disconnect in the background, and stop
the generator once received. Since this requires receiving data from the socket, it can
lead to data loss if the application is attempting to read from the same socket
simultaneously.

.. tip::
    To prevent data loss, by default, ``websocket_stream`` will raise an
    exception if it receives any data while listening for client disconnects. If
    incoming data should be ignored, ``allow_data_discard`` should be set to ``True``

If receiving data while streaming is desired,
:func:`~litestar.handlers.send_websocket_stream` can be configured to not listen for
disconnects by setting ``listen_for_disconnect=False``.

.. important::
    When using ``listen_for_disconnect=False``, the application needs to ensure the
    disconnect event is received elsewhere, otherwise the stream will only terminate
    when the generator is exhausted


Combining streaming and receiving data
---------------------------------------

To stream and receive data concurrently, the stream can be set up manually using
:func:`~litestar.handlers.send_websocket_stream` in combination with either a regular
:class:`~litestar.handlers.websocket` handler or a WebSocket listener.

.. tab-set::

    .. tab-item:: websocket_listener

        .. literalinclude:: /examples/websockets/stream_and_receive_listener.py
            :language: python

    .. tab-item:: websocket handler

        .. literalinclude:: /examples/websockets/stream_and_receive_raw.py
            :language: python


Transport modes
---------------

WebSockets have two transport modes: ``text`` and ``binary``. They dictate how bytes are
transferred over the wire and can be set independently from another, i.e. a socket can
send ``binary`` and receive ``text``


It may seem intuitive that ``text`` and ``binary`` should map to :class:`str` and
:class:`bytes` respectively, but this is not the case. WebSockets can receive and
send data in any format, independently of the mode. The mode only affects how the
bytes are handled during transport (i.e. on the protocol level). In most cases the
default mode - ``text`` - is all that's needed. Binary transport is usually employed
when sending binary blobs that don't have a meaningful string representation, such
as images.
