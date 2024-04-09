WebSockets
==========


Handling WebSocket in an application often involves dealing with low level constructs
such as the socket itself, setting up a loop and listening for incoming data, handling
exceptions, and parsing incoming and serializing outgoing data. In addition to the
low-level :class:`websocket route handler <.handlers.websocket>`, Litestar offers two
high level interfaces:

- :class:`websocket_listener <.handlers.websocket_listener>`
- :class:`WebSocketListener <.handlers.WebsocketListener>`


These treat a WebSocket handler like any other route handler; As a callable that takes
in incoming data in an already pre-processed form and returns data to be serialized and
sent over the connection. The low level details will be handled behind the curtains.


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
    Contrary to websocket route handlers, function decorated with
    :class:`websocket_listener <.handlers.websocket_listener>` don't have to be
    asynchronous.



Receiving data
--------------

Data can be received in listener via the ``data`` parameter. The data passed to this
will be converted / parsed according to the given type annotation and supports
:class:`str`, :class:`bytes`, or arbitrary :class:`dict`\ s / or :class:`list`\ s in the
form of JSON.

.. tab-set::

    .. tab-item:: JSON

        .. literalinclude:: /examples/websockets/receive_json.py
            :language: python


    .. tab-item:: Text

        .. literalinclude:: /examples/websockets/receive_str.py


    .. tab-item:: Bytes

        .. literalinclude:: /examples/websockets/receive_bytes.py


.. important::

    Contrary to route handlers, JSON data will only be parsed but not validated. This
    is a currently limitation of the implementation and will change in future versions.


Sending data
------------

Sending data is done by simply returning the value to be sent from the handler function.
Similar to receiving data, type annotations configure how the data is being handled.
Values are are not :class:`str` or :class:`bytes` are assumed to be JSON encodable and
will be serialized accordingly before being sent. This serialization is available for
all data types currently supported by Litestar (
:doc:`dataclasses <python:library/dataclasses>`\ , :class:`TypedDict <typing.TypedDict>`,
:class:`NamedTuple <typing.NamedTuple>`,  :class:`msgspec.Struct`, etc.).


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


Transport modes
---------------

WebSockets have two transport modes: Text and binary. These can be specified
individually for receiving and sending data.

.. note::
    It may seem intuitive that ``text`` and ``binary`` should map to :class:`str` and
    :class:`bytes` respectively, but this is not the case. Listeners can receive and
    send data in any format, independently of the mode. The mode only affects how
    data is encoded during transport (i.e. on the protocol level). In most cases the
    default mode - ``text`` - is all that's needed. Binary transport is usually employed
    when sending binary blobs that don't have a meaningful string representation, such
    as images.



Setting the receive mode
++++++++++++++++++++++++

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
    it will not respond to websocket events sending data in the text channel


Setting the send mode
++++++++++++++++++++++

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
--------------------

:doc:`dependency-injection` is available as well and generally works the same as with
regular route handlers:

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
---------------------------------------

Sometimes access to the socket instance is needed, in which case the
:class:`WebSocket <.connection.WebSocket>` instance can be injected into the handler
function via the ``socket`` argument:

.. literalinclude:: /examples/websockets/socket_access.py
    :language: python


.. important::
    Since websockets are inherently asynchronous, to interact with the asynchronous
    methods on :class:`WebSocket <.connection.WebSocket>`, the handler function needs
    to be asynchronous.


Customising connection acceptance
---------------------------------

By default, Litestar will accept all incoming connections by awaiting ``WebSocket.accept()`` without arguments.
This behavior can be customized by passing a custom ``connection_accept_handler`` function. Litestar will await this
function to accept the connection.

.. literalinclude:: /examples/websockets/setting_custom_connection_headers.py
    :language: python


Class based WebSocket handling
------------------------------

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
----------------

.. versionadded:: 2.7.0

Litestar supports custom ``websocket_class`` instances, which can be used to further configure the default :class:`WebSocket`.
The example below illustrates how to implement custom websocket class for the whole application.

.. dropdown:: Example of a custom websocket at the application level

    .. literalinclude:: /examples/websockets/custom_websocket.py
        :language: python

.. admonition:: Layered architecture

   WebSocket classes are part of Litestar's layered architecture, which means you can
   set a websocket class on every layer of the application. If you have set a webscoket
   class on multiple layers, the layer closest to the route handler will take precedence.

   You can read more about this in the :ref:`usage/applications:layered architecture` section
