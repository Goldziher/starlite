Events
======

Litestar supports a simple implementation of the event emitter / listener pattern:

.. literalinclude:: /examples/events/event_base.py
    :language: python


The above example illustrates the power of this pattern - it allows us to perform async operations without blocking,
and without slowing down the response cycle.

Listening to Multiple Events
++++++++++++++++++++++++++++

Event listeners can listen to multiple events:

.. literalinclude:: /examples/events/event_base.py
    :caption: Multiple events
    :language: python


Using Multiple Listeners
++++++++++++++++++++++++

You can also listen to the same events using multiple listeners:

.. literalinclude:: /examples/events/multiple_listeners.py
    :caption: Multiple listeners
    :language: python


In the above example we are performing two side effect for the same event, one sends the user an email, and the other
sending an HTTP request to a service management system to create an issue.

Passing Arguments to Listeners
++++++++++++++++++++++++++++++

The method :meth:`emit <litestar.events.BaseEventEmitterBackend.emit>` has the following signature:

.. literalinclude:: /examples/events/argument_to_listener.py
    :caption: Passing arguments to listeners
    :language: python


This means that it expects a string for ``event_id`` following by any number of positional and keyword arguments. While
this is highly flexible, it also means you need to ensure the listeners for a given event can handle all the expected args
and kwargs.

For example, the following would raise an exception in python:

.. literalinclude:: /examples/events/listener_exception.py
    :language: python


The reason for this is that both listeners will receive two kwargs - ``email`` and ``reason``. To avoid this, the previous example
had ``**kwargs`` in both:


.. literalinclude:: /examples/events/listener_no_exception.py
    :language: python


Creating Event Emitters
-----------------------

An "event emitter" is a class that inherits from
:class:`BaseEventEmitterBackend <litestar.events.BaseEventEmitterBackend>`, which
itself inherits from :obj:`contextlib.AbstractAsyncContextManager`.

- :meth:`emit <litestar.events.BaseEventEmitterBackend.emit>`: This is the method that performs the actual emitting
  logic.

Additionally, the abstract ``__aenter__`` and ``__aexit__`` methods from
:obj:`contextlib.AbstractAsyncContextManager` must be implemented, allowing the
emitter to be used as an async context manager.

By default Litestar uses the
:class:`SimpleEventEmitter <litestar.events.SimpleEventEmitter>`, which offers an
in-memory async queue.

This solution works well if the system does not need to rely on complex behaviour, such as a retry
mechanism, persistence, or scheduling/cron. For these more complex use cases, users should implement their own backend
using either a DB/Key store that supports events (Redis, Postgres, etc.), or a message broker, job queue, or task queue
technology.
