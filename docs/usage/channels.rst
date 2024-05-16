.. currentmodule:: litestar.channels

Channels
========

**Channels** are a group of related functionalities, built to facilitate the routing
of event streams, which for example can be used to broadcast messages to WebSocket
clients.

Channels provide:

1. Independent :term:`broker` backends, optionally handling inter-process communication
   and data persistence on demand
2. "Channel" based subscription management
3. Subscriber objects as an abstraction over an individualized :term:`event stream`,
   providing background workers and managed subscriptions
4. Synchronous and asynchronous data publishing
5. Optional history management on a per-channel basis
6. :doc:`WebSocket </usage/websockets>` integration, generating WebSocket route
   handlers for an application, to handle the subscription and publishing of incoming
   events to the connected client


Basic concepts
--------------

Utilizing channels involves a few moving parts, of which the most important ones are:

.. glossary::

    event
        A single piece of data published to, or received from a :term:`backend` bound
        to the channel it was originally published to

    event stream
        A stream of :term:`events <event>`, consisting of events from all the channels a
        :term:`Subscriber` has previously subscribed to

    subscriber
        A :class:`Subscriber <.subscriber.Subscriber>`: An object wrapping an
        :term:`event stream` and providing access to it through various methods

    backend
        A :class:`ChannelsBackend <.backends.base.ChannelsBackend>`. This object
        manages communication between the plugin and the :term:`broker`, publishing
        messages to and receiving messages from it. Each plugin instance is associated
        with exactly one backend.

    broker
        Responsible for receiving and publishing messages to all connected
        :term:`backends <backend>`; All backends sharing the same broker will have
        access to the same messages, allowing for inter-process communication. This is
        typically handled by a separate entity like `Redis <https://redis.io/>`_

    plugin
        The :class:`ChannelsPlugin <.plugin.ChannelsPlugin>`, a central instance
        managing :term:`subscribers <subscriber>`, reading messages from the
        :term:`backend`, putting them in the appropriate :term:`event stream`, and
        publishing data to the backend


Flowcharts
++++++++++


.. mermaid::
    :align: center
    :caption: Publishing flow from the application to the :term:`broker`

    flowchart LR
        Backend(Backend) --> Broker[(Broker)]

        Plugin{{Plugin}} --> Backend

        Application[[Application]] --> Plugin


.. mermaid::
    :align: center
    :caption: Fanout flow of data from the :term:`broker` to the sockets, showing multiple plugin instances

    flowchart TD
        Broker[(Broker)]

        Broker --> Backend_1(Backend)
        Broker --> Backend_2(Backend)

        Backend_1 --> Plugin_1{{Plugin}}
        Backend_2 --> Plugin_2{{Plugin}}

        Plugin_1 --> Subscriber_1[Subscriber]
        Plugin_1 --> Subscriber_2[Subscriber]
        Plugin_1 --> Subscriber_3[Subscriber]

        Plugin_2 --> Subscriber_4[Subscriber]
        Plugin_2 --> Subscriber_5[Subscriber]
        Plugin_2 --> Subscriber_6[Subscriber]


The ``ChannelsPlugin``
----------------------

.. currentmodule:: litestar.channels.plugin

The :class:`ChannelsPlugin` acts as the central entity for managing channels and
subscribers. It's used to publish messages, control how data is stored, and manage
subscribers, route handlers, and configuration.


.. tip::
    The plugin makes itself available as a dependency under the ``channels`` key, which
    means it's not necessary to import it and instead, it can be used from within route
    handlers or other callables within the dependency tree directly


Configuring the channels
+++++++++++++++++++++++++

The channels managed by the plugin can be either defined upfront, passing them to the
``channels`` argument, or created "on the fly" (i.e. on the first subscription to a
channel) by setting ``arbitrary_channels_allowed=True``.


.. literalinclude:: /examples/channels/passing_channels_explicitly.py
    :caption: Passing channels explicitly
    :language: python


.. literalinclude:: /examples/channels/allowing_arbitrary_channels.py
    :caption: Allowing arbitrary channels
    :language: python


If ``arbitrary_channels_allowed`` is not ``True``, trying to publish or subscribe to a
channel not passed to ``channels`` will raise a :exc:`ChannelsException`.


Publishing data
+++++++++++++++


One of the core aspects of the plugin is publishing data, which is done through its
:meth:`publish <ChannelsPlugin.publish>` method:

.. literalinclude:: /examples/channels/publish_data.py
    :caption: Publish data
    :language: python


The above example will publish the data to the channel ``general``, subsequently putting
it into all subscriber's :term:`event stream` to be consumed.

This method is non-blocking, even though channels and the associated
:term:`backends <backend>` are fundamentally asynchronous.

Calling ``publish`` effectively enqueues a message to be sent to the backend, from which
follows that there's no guarantee that an event will be available in the backend
immediately after this call.

Alternatively, the asynchronous :meth:`wait_published <ChannelsPlugin.wait_published>`
method can be used, which skips the internal message queue, publishing the data to the
backend directly.

.. note::
    While calling :meth:`publish <ChannelsPlugin.publish>` does not guarantee the
    message is sent to the backend immediately, it will be sent there *eventually*; On
    shutdown, the plugin will wait for all queues to empty


Managing subscriptions
++++++++++++++++++++++

Another core functionality of the plugin is managing subscriptions, for which two
different approaches exist:

1. Manually through the :meth:`subscribe <ChannelsPlugin.subscribe>` and
   :meth:`unsubscribe <ChannelsPlugin.unsubscribe>` methods
2. By using the :meth:`start_subscription <ChannelsPlugin.start_subscription>` context
   manager

Both :meth:`subscribe <ChannelsPlugin.subscribe>` and
:meth:`start_subscription <ChannelsPlugin.start_subscription>` produce a
:class:`Subscriber`, which can be used to interact with the streams of events subscribed
to.

The context manager should be preferred, since it ensures that channels are being
unsubscribed. Using the ``subscriber`` and ``unsubscribe`` methods directly should only
be done when a context manager cannot be used, e.g. when the subscription would span
different contexts.

.. literalinclude:: /examples/channels/subscribe_method_manually.py
    :caption: Calling the subscription methods manually
    :language: python


.. literalinclude:: /examples/channels/subscribe_method_manually.py
    :caption: Using the context manager
    :language: python


It is also possible to unsubscribe from individual channels, which may be desirable if
subscriptions need to be managed dynamically.

.. literalinclude:: /examples/channels/unsubscribe_method_manually.py
    :caption: Calling the unsubscription methods manually
    :language: python


Or, using the context manager

.. literalinclude:: /examples/channels/subscribe_method_context_manager.py
    :caption: Using the context manager
    :language: python


Managing history
+++++++++++++++++

Some backends support per-channel history, keeping a certain amount of
:term:`events <event>` in storage. This history can then be pushed to a
:term:`subscriber`.

The plugin's :meth:`put_subscriber_history <ChannelsPlugin.put_subscriber_history>` can
be used to fetch this history and put it into a subscriber's :term:`event stream`.

.. literalinclude:: /examples/channels/put_history.py
    :language: python


.. note::
    The publication of the history happens sequentially, one channel and one
    event at a time. This is done to ensure the correct ordering of events and to avoid
    filling up a subscriber's backlog, which would result in dropped history entries. Should the
    amount of entries exceed the maximum backlog size, the execution will wait until
    previous events have been processed.

    .. seealso::

        * `Managing backpressure`_


The ``Subscriber``
------------------

.. py:currentmodule:: litestar.channels.subscriber

The :class:`Subscriber` manages an individual :term:`event stream`, provided to it by
the plugin, representing the sum of events from all channels the subscriber has
subscribed to.

It can be considered the endpoint of all events, while the backends act as the source,
and the plugin as a router, being responsible for supplying events gathered from the
backend into the appropriate subscriber's streams.

In addition to being an abstraction of an :term:`event stream`, the :class:`Subscriber`
provides two methods to handle this stream:

:meth:`iter_events <Subscriber.iter_events>`
    An asynchronous generator, producing one event from the stream at a time, waiting
    until the next one becomes available

:meth:`run_in_background <Subscriber.run_in_background>`
    A context manager, wrapping an :class:`asyncio.Task`, consuming events yielded by
    :meth:`iter_events <Subscriber.iter_events>`, invoking a provided callback for each
    of them. Upon exit, it will attempt a graceful shutdown of the running task, waiting
    for all currently enqueued events in the stream to be processed. If the context
    exits with an error, the task will be cancelled instead.

    .. tip::
        It's possible to force the task to stop immediately, by passing ``join=False`` to
        :meth:`run_in_background <Subscriber.run_in_background>`, which will
        lead to the cancellation of the task. By default this only happens when the context is
        left with an exception.


.. important::
    The :term:`events <event>` in the :term:`event streams <event stream>` are always
    bytes; When calling :meth:`ChannelsPlugin.publish`, data will be serialized before
    being sent to the backend.


Consuming the event stream
+++++++++++++++++++++++++++

There are two general methods of consuming the :term:`event stream`:

1. By iterating over it directly, using :meth:`iter_events <Subscriber.iter_events>`
2. By using the :meth:`run_in_background <Subscriber.run_in_background>` context manager,
   which starts a background task, iterating over the stream, invoking a provided
   callback for every :term:`event` received

Iterating over the stream directly is mostly useful if processing the events is the only
concern, since :meth:`iter_events <Subscriber.iter_events>` is effectively an infinite
loop. For all other applications, using the context manager is preferable, since it
allows to easily run other code concurrently.


.. literalinclude:: /examples/channels/iter_stream.py
    :language: python


In the above example, the stream is used to send data to a
:class:`WebSocket <litestar.connection.WebSocket>`.

The same can be achieve by passing
:meth:`WebbSocket.send_text <litestar.connection.WebSocket.send_text>` as the callback
to :meth:`run_in_background <Subscriber.run_in_background>`. This will cause the
WebSocket's method to be invoked every time a new event becomes available in the stream,
but gives control back to the application, providing an opportunity to perform other
tasks, such as receiving incoming data from the socket.


.. literalinclude:: /examples/channels/run_in_background.py
    :language: python


.. important::
    Iterating over :meth:`iter_events <Subscriber.iter_events>` should be approached
    with caution when being used together with WebSockets.

    Since :exc:`WebSocketDisconnect` is only raised after the corresponding ASGI event
    has been *received*, it can result in an indefinitely suspended coroutine. This can
    happen if for example the client disconnects, but no further events are received.
    The generator will then wait for new events, but since it will never receive any,
    no ``send`` call on the WebSocket will be made, which in turn means no exception
    will be raised to break the loop.



Managing backpressure
---------------------

Each subscriber manages its own backlog: A queue of unprocessed :term:`events <event>`.
By default, this backlog is unlimited in size, allowing it to grow indefinitely. For
most applications, this should be no issue, but when the recipient consistently can't
process messages faster than they come in, an application might opt to handle this case.

The channels plugin provides two different strategies for managing this backpressure:

1. A backoff strategy, dropping newly incoming messages as long as the backlog is full
2. An eviction strategy, dropping the oldest message in the backlog when a new one is
   added while the backlog is full


.. literalinclude:: /examples/channels/backoff_strategy.py
    :caption: Backoff strategy
    :language: python


.. literalinclude:: /examples/channels/eviction_strategy.py
    :caption: Eviction strategy
    :language: python


Backends
--------

The storing and fanout of messages is handled by a
:class:`ChannelsBackend <litestar.channels.backends.base.ChannelsBackend>`. Currently
implemented are:

:class:`MemoryChannelsBacked <.memory.MemoryChannelsBackend>`
    A basic in-memory backend, mostly useful for testing and local development, but
    still fully capable. Since it stores all data in-process, it can achieve the highest
    performance of all the backends, but at the same time is not suitable for
    applications running on multiple processes.

:class:`RedisChannelsPubSubBackend <.redis.RedisChannelsPubSubBackend>`
    A Redis based backend, using `Pub/Sub <https://redis.io/docs/manual/pubsub/>`_ to
    delivery messages. This Redis backend has a low latency and overhead and is
    generally recommended if history is not needed

:class:`RedisChannelsStreamBackend <.redis.RedisChannelsStreamBackend>`
    A redis based backend, using `streams <https://redis.io/docs/data-types/streams/>`_
    to deliver messages. It has a slightly higher latency when publishing than the
    Pub/Sub backend, but achieves the same throughput in message fanout. Recommended
    when history is needed


:class:`AsyncPgChannelsBackend <.asyncpg.AsyncPgChannelsBackend>`
    A postgres backend using the
    `asyncpg <https://magicstack.github.io/asyncpg/current/>`_ driver


:class:`PsycoPgChannelsBackend <.psycopg.PsycoPgChannelsBackend>`
    A postgres backend using the `psycopg3 <https://www.psycopg.org/psycopg3/docs/>`_
    async driver




Integrating with websocket handlers
-----------------------------------


Generating route handlers
+++++++++++++++++++++++++

A common pattern is to create a route handler per channel, sending data to the connected
client from that channel. This can be fully automated, using the plugin to create these
route handlers.

.. literalinclude:: /examples/channels/create_route_handlers.py
    :language: python
    :caption: Setting ``create_route_handlers=True`` will create route handlers for all ``channels``



The generated route handlers can optionally be configured to send the channel's history
after a client has connected:

.. literalinclude:: /examples/channels/create_route_handlers_send_history.py
    :language: python
    :caption: Sending the first 10 history entries after a client connects


.. tip::

    When using the ``arbitrary_channels_allowed`` flag on the :class:`ChannelsPlugin`, a
    single route handler will be generated instead, using a
    :ref:`path parameter <usage/routing/parameters:path parameters>` to specify the channel name
