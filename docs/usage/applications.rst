Applications
=============

Application objects
-------------------

At the root of every Litestar application is an instance of the :class:`~litestar.app.Litestar`
class. Typically, this code will be placed in a file called ``main.py``, ``app.py``, ``asgi.py`` or similar
at the project's root directory.

These entry points are also used during :ref:`CLI autodiscovery <usage/cli:autodiscovery>`

Creating an app is straightforward – the only required :term:`args <argument>` is a :class:`list`
of :class:`Controllers <.controller.Controller>`, :class:`Routers <.router.Router>`,
or :class:`Route handlers <.handlers.BaseRouteHandler>`:

.. literalinclude:: /examples/hello_world.py
    :caption: A simple Hello World Litestar app
    :language: python

The app instance is the root level of the app - it has the base path of ``/`` and all root level
:class:`Controllers <.controller.Controller>`, :class:`Routers <.router.Router>`,
and :class:`Route handlers <.handlers.BaseRouteHandler>` should be registered on it.

.. seealso:: To learn more about registering routes, check out this chapter in the documentation:

    * :ref:`Routing - Registering Routes <usage/routing/overview:Registering Routes>`

Startup and Shutdown
--------------------

You can pass a list of :term:`callables <python:callable>` - either sync or async functions, methods, or class instances
- to the :paramref:`~litestar.app.Litestar.on_startup` / :paramref:`~litestar.app.Litestar.on_shutdown`
:term:`kwargs <argument>` of the :class:`app <litestar.app.Litestar>` instance. Those will be called in
order, once the ASGI server such as `uvicorn <https://www.uvicorn.org/>`_,
`Hypercorn <https://hypercorn.readthedocs.io/en/latest/#/>`_, `Granian <https://github.com/emmett-framework/granian/>`_,
`Daphne <https://github.com/django/daphne/>`_, etc. emits the respective event.

.. mermaid::

   flowchart LR
       Startup[ASGI-Event: lifespan.startup] --> on_startup
       Shutdown[ASGI-Event: lifespan.shutdown] --> on_shutdown

A classic use case for this is database connectivity. Often, we want to establish a database connection on application
startup, and then close it gracefully upon shutdown.

For example, let us create a database connection using the async engine from
`SQLAlchemy <https://docs.sqlalchemy.org/en/latest/orm/extensions/asyncio.html>`_. We create two functions, one to get or
establish the connection, and another to close it, and then pass them to the :class:`~litestar.app.Litestar` constructor:

.. literalinclude:: /examples/startup_and_shutdown.py
    :caption: Startup and Shutdown
    :language: python

.. _lifespan-context-managers:

Lifespan context managers
-------------------------

In addition to the lifespan hooks, Litestar also supports managing the lifespan of an application using an
:term:`asynchronous context manager`. This can be useful when dealing with long running tasks, or those that need to
keep a certain context object, such as a connection, around.

.. literalinclude:: /examples/application_hooks/lifespan_manager.py
    :caption: Handling a database connection
    :language: python

Order of execution
------------------

When multiple lifespan context managers and :paramref:`~litestar.app.Litestar.on_shutdown`  hooks are specified,
Litestar will invoke the :term:`context managers <asynchronous context manager>` in inverse order before the
shutdown hooks are invoked.

Consider the case where there are two lifespan context managers ``ctx_a`` and ``ctx_b`` as well as two shutdown hooks
``hook_a`` and ``hook_b`` as shown in the following code:

.. literalinclude:: /examples/execution_order.py
    :caption: Example of multiple :term:`context managers <asynchronous context manager>` and shutdown hooks
    :language: python


During shutdown, they are executed in the following order:

.. mermaid::

    flowchart LR
        ctx_b --> ctx_a --> hook_a --> hook_b

As seen, the :term:`context managers <asynchronous context manager>` are invoked in inverse order.
On the other hand, the shutdown hooks are invoked in their specified order.

.. _application-state:

Using Application State
-----------------------

As seen in the examples for the `on_startup / on_shutdown <#startup-and-shutdown>`_, :term:`callables <python:callable>`
passed to these hooks can receive an optional :term:`kwarg <argument>` called ``app``, through which the application's
state object and other properties can be accessed. The advantage of using application :paramref:`~.app.Litestar.state`,
is that it can be accessed during multiple stages of the connection, and it can be injected into dependencies and
route handlers.

The Application State is an instance of the :class:`.datastructures.state.State` datastructure, and it is
accessible via the :paramref:`~.app.Litestar.state` attribute. As such it can be accessed wherever the app instance
is accessible.

:paramref:`~.app.Litestar.state` is one of the
:ref:`reserved keyword arguments <usage/routing/handlers:"reserved" keyword arguments>`.

It is important to understand in this context that the application instance is injected into the ASGI ``scope`` mapping
for each connection (i.e. request or websocket connection) as ``scope["app"]``. This makes the application
accessible wherever the scope mapping is available, e.g. in middleware, on :class:`~.connection.request.Request` and
:class:`~.connection.websocket.WebSocket` instances (accessible as ``request.app`` / ``socket.app``), and many
other places.

Therefore, :paramref:`~.app.Litestar.state` offers an easy way to share contextual data between disparate parts
of the application, as seen below:

.. literalinclude:: /examples/application_state/using_application_state.py
    :caption: Using Application State
    :language: python

.. _Initializing Application State:

Initializing Application State
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To seed application state, you can pass a :class:`~.datastructures.state.State` object to the
:paramref:`~.app.Litestar.state` parameter of the Litestar constructor:

.. literalinclude:: /examples/application_state/passing_initial_state.py
    :caption: Using Application State
    :language: python

.. note:: :class:`~.datastructures.state.State` can be initialized with a :class:`dictionary <dict>`, an instance of
    :class:`~.datastructures.state.ImmutableState` or :class:`~.datastructures.state.State`,
    or a :class:`list` of :class:`tuples <tuple>` containing key/value pairs.

You may instruct :class:`~.datastructures.state.State` to deep copy initialized data to prevent mutation from outside
the application context.

To do this, set :paramref:`~.datastructures.state.State.deep_copy` to ``True`` in the
:class:`~.datastructures.state.State` constructor.

Injecting Application State into Route Handlers and Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As seen in the above example, Litestar offers an easy way to inject state into route handlers and dependencies - simply
by specifying ``state`` as a kwarg to the handler or dependency function. For example:

.. literalinclude:: /examples/application_state/injecting_application_state.py
    :caption: Accessing application :class:`~.datastructures.state.State` in a handler function
    :language: python


When using this pattern you can specify the class to use for the state object. This type is not merely for type
checkers, rather Litestar will instantiate a new ``state`` instance based on the type you set there.
This allows users to use custom classes for :class:`~.datastructures.state.State`.

While this is very powerful, it might encourage users to follow anti-patterns: it is important to emphasize that using
state can lead to code that is hard to reason about and bugs that are difficult to understand, due to changes in
different ASGI contexts. As such, this pattern should be used only when it is the best choice and in a limited fashion.
To discourage its use, Litestar also offers a builtin :class:`~.datastructures.state.ImmutableState` class.
You can use this class to type state and ensure that no mutation of state is allowed:

.. literalinclude:: /examples/application_state/using_immutable_state.py
    :caption: Using Custom State to ensure immutability
    :language: python


Application Hooks
-----------------

Litestar includes several application level hooks that allow users to run their own sync or async
:term:`callables <python:callable>`. While you are free to use these hooks as you see fit, the design intention
behind them is to allow for easy instrumentation for observability (monitoring, tracing, logging, etc.).

.. note:: All application hook kwargs detailed below receive either a single :term:`python:callable` or a :class:`list`
    of :term:`callables <python:callable>`.
    If a :class:`list` is provided, it is called in the order it is given.

After Exception
^^^^^^^^^^^^^^^

The :paramref:`~litestar.app.Litestar.after_exception` hook takes a
:class:`sync or async callable <litestar.types.AfterExceptionHookHandler>` that is called with two arguments:
the ``exception`` that occurred and the ASGI ``scope`` of the request or websocket connection.

.. literalinclude:: /examples/application_hooks/after_exception_hook.py
    :caption: After Exception Hook
    :language: python

.. attention:: This hook is not meant to handle exceptions - it just receives them to allow for side effects.
    To handle exceptions you should define :ref:`exception handlers <usage/exceptions:exception handling>`.

Before Send
^^^^^^^^^^^

The :paramref:`~litestar.app.Litestar.before_send` hook takes a
:class:`sync or async callable <litestar.types.BeforeMessageSendHookHandler>` that is called when an ASGI message is
sent. The hook receives the message instance and the ASGI ``scope``.

.. literalinclude:: /examples/application_hooks/before_send_hook.py
    :caption: Before Send Hook
    :language: python

Initialization
^^^^^^^^^^^^^^

Litestar includes a hook for intercepting the arguments passed to the
:class:`Litestar constructor <litestar.app.Litestar>`, before they are used to instantiate the application.

Handlers can be passed to the :paramref:`~.app.Litestar.on_app_init` parameter on construction of the application,
and in turn, each will receive an instance of :class:`~.config.app.AppConfig` and must return an instance of same.

This hook is useful for applying common configuration between applications, and for use by developers who may wish to
develop third-party application configuration systems.

.. note:: :paramref:`~.app.Litestar.on_app_init` handlers cannot be :ref:`python:async def` functions, as they are
    called within :paramref:`~litestar.app.Litestar.__init__`, outside of an async context.

.. literalinclude:: /examples/application_hooks/on_app_init.py
    :caption: Example usage of the ``on_app_init`` hook to modify the application configuration.
    :language: python

.. _layered-architecture:

Layered architecture
--------------------

Litestar has a layered architecture compromising of 4 layers:

#. :class:`The application object <litestar.app.Litestar>`
#. :class:`Routers <.router.Router>`
#. :class:`Controllers <.controller.Controller>`
#. :class:`Handlers <.handlers.BaseRouteHandler>`

There are many :term:`parameters <parameter>` that can be defined on every layer, in which case the :term:`parameter`
defined on the layer **closest to the handler** takes precedence. This allows for maximum
flexibility and simplicity when configuring complex applications and enables transparent
overriding of parameters.

Parameters that support layering are:

* :ref:`after_request <after_request>`
* :ref:`after_response <after_response>`
* :ref:`before_request <before_request>`
* :ref:`cache_control <usage/responses:cache control>`
* :doc:`dependencies </usage/dependency-injection>`
* :doc:`dto </usage/dto/0-basic-use>`
* :ref:`etag <usage/responses:etag>`
* :doc:`exception_handlers </usage/exceptions>`
* :doc:`guards </usage/security/guards>`
* :ref:`include_in_schema <usage/openapi/schema_generation:configuring schema generation on a route handler>`
* :doc:`middleware </usage/middleware/index>`
* :ref:`opt <handler_opts>`
* :ref:`request_class <usage/requests:custom request>`
* :ref:`response_class <usage/responses:custom responses>`
* :ref:`response_cookies <usage/responses:setting response cookies>`
* :ref:`response_headers <usage/responses:setting response headers>`
* :doc:`return_dto </usage/dto/0-basic-use>`
* ``security``
* ``tags``
* ``type_decoders``
* ``type_encoders``
* :ref:`websocket_class <usage/websockets:custom websocket>`
