Route handlers
==============

Route handlers are the core of Litestar. They are constructed by decorating a function or class method with one of the
handler :term:`decorators <decorator>` exported from Litestar.

For example:

.. literalinclude:: /examples/routing/handler.py
    :caption: Defining a route handler by decorating a function with the :class:`@get() <.handlers.get>` :term:`decorator`
    :language: python


In the above example, the :term:`decorator` includes all the information required to define the endpoint operation for
the combination of the path ``"/"`` and the HTTP verb ``GET``. In this case it will be a HTTP response with a
``Content-Type`` header of ``text/plain``.

.. include:: /admonitions/sync-to-thread-info.rst

Declaring paths
---------------

All route handler :term:`decorators <decorator>` accept an optional path :term:`argument`.
This :term:`argument` can be declared as a :term:`kwarg <argument>` using the
:paramref:`~.handlers.base.BaseRouteHandler.path` parameter:

.. literalinclude:: /examples/routing/declaring_path.py
    :caption: Defining a route handler by passing the path as a keyword argument
    :language: python


It can also be passed as an :term:`argument` without the keyword:

.. literalinclude:: /examples/routing/declaring_path_argument.py
    :caption: Defining a route handler but not using the keyword argument
    :language: python


And the value for this :term:`argument` can be either a string path, as in the above examples, or a :class:`list` of
:class:`string <str>`  paths:

.. literalinclude:: /examples/routing/declaring_multiple_paths.py
    :caption: Defining a route handler with multiple paths
    :language: python


This is particularly useful when you want to have optional
:ref:`path parameters <usage/routing/parameters:Path Parameters>`:

.. literalinclude:: /examples/routing/declaring_path_optional_parameter.py
    :caption: Defining a route handler with a path that has an optional path parameter
    :language: python


.. _handler-function-kwargs:

"reserved" keyword arguments
----------------------------

Route handler functions or methods access various data by declaring these as annotated function :term:`kwargs <argument>`. The annotated
:term:`kwargs <argument>` are inspected by Litestar and then injected into the request handler.

The following sources can be accessed using annotated function :term:`kwargs <argument>`:

- :ref:`path, query, header, and cookie parameters <usage/routing/parameters:the parameter function>`
- :doc:`requests </usage/requests>`
- :doc:`injected dependencies </usage/dependency-injection>`

Additionally, you can specify the following special :term:`kwargs <argument>`,
(known as "reserved keywords"):

* ``cookies``: injects the request :class:`cookies <.datastructures.cookie.Cookie>` as a parsed
  :class:`dictionary <dict>`.
* ``headers``: injects the request headers as a parsed :class:`dictionary <dict>`.
* ``query`` : injects the request ``query_params`` as a parsed :class:`dictionary <dict>`.
* ``request``: injects the :class:`Request <.connection.Request>` instance. Available only for `HTTP route handlers`_
* ``scope`` : injects the ASGI scope :class:`dictionary <dict>`.
* ``socket``: injects the :class:`WebSocket <.connection.WebSocket>` instance. Available only for `websocket route handlers`_
* ``state`` : injects a copy of the application :class:`State <.datastructures.state.State>`.
* ``body`` : the raw request body. Available only for `HTTP route handlers`_

Note that if your parameters collide with any of the reserved :term:`keyword arguments <argument>` above, you can
:ref:`provide an alternative name <usage/routing/parameters:Alternative names and constraints>`.

For example:

.. literalinclude:: /examples/routing/reserved_keyword_argument.py
    :caption: Providing an alternative name for a reserved keyword argument
    :language: python


.. tip:: You can define a custom typing for your application state and then use it as a type instead of just using the
    :class:`~.datastructures.state.State` class from Litestar

Type annotations
----------------

Litestar enforces strict :term:`type annotations <annotation>`.
Functions decorated by a route handler **must** have all their :term:`arguments <argument>` and return
value type annotated.

If a type annotation is missing, an :exc:`~.exceptions.ImproperlyConfiguredException` will be raised during the
application boot-up process.

There are several reasons for why this limitation is enforced:

#. To ensure best practices
#. To ensure consistent OpenAPI schema generation
#. To allow Litestar to compute the :term:`arguments <argument>` required by a function during application bootstrap

HTTP route handlers
-------------------

The most commonly used route handlers are those that handle HTTP requests and responses.
These route handlers all inherit from the :class:`~.handlers.HTTPRouteHandler` class, which is aliased as the
:term:`decorator` called :func:`~.handlers.route`:

.. literalinclude:: /examples/routing/route_handler_http_1.py
    :caption: Defining a route handler by decorating a function with the :class:`@route() <.handlers.route>`
    :language: python


As mentioned above, :func:`@route() <.handlers.route>` is merely an alias for ``HTTPRouteHandler``,
thus the below code is equivalent to the one above:

.. literalinclude:: /examples/routing/route_handler_http_2.py
    :caption: Defining a route handler by decorating a function with the
    :language: python


Semantic handler :term:`decorators <decorator>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Litestar also includes "semantic" :term:`decorators <decorator>`, that is, :term:`decorators <decorator>` the pre-set
the :paramref:`~litestar.handlers.HTTPRouteHandler.http_method` :term:`kwarg <argument>` to a specific HTTP verb,
which correlates with their name:

* :func:`@delete() <.handlers.delete>`
* :func:`@get() <.handlers.get>`
* :func:`@head() <.handlers.head>`
* :func:`@patch() <.handlers.patch>`
* :func:`@post() <.handlers.post>`
* :func:`@put() <.handlers.put>`

These are used exactly like :func:`@route() <.handlers.route>` with the sole exception that you cannot configure the
:paramref:`~.handlers.HTTPRouteHandler.http_method` :term:`kwarg <argument>`:

.. dropdown:: Click to see the predefined route handlers

    .. literalinclude:: /examples/routing/handler_decorator.py
        :caption: Predefined :term:`decorators <decorator>` for HTTP route handlers
        :language: python


Although these :term:`decorators <decorator>` are merely subclasses of :class:`~.handlers.HTTPRouteHandler` that pre-set
the :paramref:`~.handlers.HTTPRouteHandler.http_method`, using :func:`@get() <.handlers.get>`,
:func:`@patch() <.handlers.patch>`, :func:`@put() <.handlers.put>`, :func:`@delete() <.handlers.delete>`, or
:func:`@post() <.handlers.post>` instead of :func:`@route() <.handlers.route>` makes the code clearer and simpler.

Furthermore, in the OpenAPI specification each unique combination of HTTP verb (e.g. ``GET``, ``POST``, etc.) and path
is regarded as a distinct `operation <https://spec.openapis.org/oas/latest.html#operation-object>`_\ , and each
operation should be distinguished by a unique :paramref:`~.handlers.HTTPRouteHandler.operation_id` and optimally
also have a :paramref:`~.handlers.HTTPRouteHandler.summary` and
:paramref:`~.handlers.HTTPRouteHandler.description` sections.

As such, using the :func:`@route() <.handlers.route>` :term:`decorator` is discouraged.
Instead, the preferred pattern is to share code using secondary class methods or by abstracting code to reusable
functions.

Websocket route handlers
------------------------

A WebSocket connection can be handled with a :func:`@websocket() <.handlers.WebsocketRouteHandler>` route handler.

.. note:: The websocket handler is a low level approach, requiring to handle the socket directly,
    and dealing with keeping it open, exceptions, client disconnects, and content negotiation.

    For a more high level approach to handling WebSockets, see :doc:`/usage/websockets`

.. literalinclude:: /examples/routing/handler_websocket_1.py
    :caption: Using the :func:`@websocket() <.handlers.WebsocketRouteHandler>` route handler :term:`decorator`
    :language: python


The :func:`@websocket() <.handlers.WebsocketRouteHandler>` :term:`decorator` is an alias of the
:class:`~.handlers.WebsocketRouteHandler` class. Thus, the below code is equivalent to the one above:

.. literalinclude:: /examples/routing/handler_websocket_2.py
    :caption: Using the :class:`~.handlers.WebsocketRouteHandler` class directly
    :language: python


In difference to HTTP routes handlers, websocket handlers have the following requirements:

#. They **must** declare a ``socket`` :term:`kwarg <argument>`.
#. They **must** have a return :term:`annotation` of ``None``.
#. They **must** be :ref:`async functions <python:async def>`.

These requirements are enforced using inspection, and if any of them is unfulfilled an informative exception
will be raised.

OpenAPI currently does not support websockets. As such no schema will be generated for these route handlers.

.. seealso:: * :class:`~.handlers.WebsocketRouteHandler`
    * :doc:`/usage/websockets`

ASGI route handlers
-------------------

If you need to write your own ASGI application, you can do so using the :func:`@asgi() <.handlers.asgi>` :term:`decorator`:

.. literalinclude:: /examples/routing/handler_asgi_1.py
    :caption: Using the :func:`@asgi() <.handlers.asgi>` route handler :term:`decorator`
    :language: python


Like other route handlers, the :func:`@asgi() <.handlers.asgi>` :term:`decorator` is an alias of the
:class:`~.handlers.ASGIRouteHandler` class. Thus, the code below is equivalent to the one above:

.. literalinclude:: /examples/routing/handler_asgi_2.py
    :caption: Using the :class:`~.handlers.ASGIRouteHandler` class directly
    :language: python


Limitations of ASGI route handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In difference to the other route handlers, the :func:`@asgi() <.handlers.asgi>` route handler accepts only three
:term:`kwargs <argument>` that **must** be defined:

* ``scope``, a mapping of values describing the ASGI connection. It always includes a ``type`` key, with the values being
  either ``http`` or ``websocket``, and a ``path`` key. If the type is ``http``, the scope dictionary will also include
  a ``method`` key with the value being one of ``DELETE``, ``GET``, ``POST``, ``PATCH``, ``PUT``, ``HEAD``.
* ``receive``, an injected function by which the ASGI application receives messages.
* ``send``, an injected function by which the ASGI application sends messages.

You can read more about these in the `ASGI specification <https://asgi.readthedocs.io/en/latest/specs/main.html>`_.

Additionally, ASGI route handler functions **must** be :ref:`async functions <python:async def>`.
This is enforced using inspection, and if the function is not an :ref:`async functions <python:async def>`,
an informative exception will be raised.

See the :class:`ASGIRouteHandler API reference documentation <.handlers.asgi_handlers.ASGIRouteHandler>` for full
details on the :func:`@asgi() <.handlers.asgi>` :term:`decorator` and the :term:`kwargs <argument>` it accepts.

Route handler indexing
----------------------

You can provide a :paramref:`~.handlers.base.BaseRouteHandler.name` :term:`kwarg <argument>` in all route handler
:term:`decorators <decorator>`. The value for this :term:`kwarg <argument>` **must be unique**, otherwise
:exc:`~.exceptions.ImproperlyConfiguredException` exception will be raised.

The default value for :paramref:`~.handlers.base.BaseRouteHandler.name` is value returned by the handler's
:meth:`~object.__str__` method which should be the full dotted path to the handler
(e.g., ``app.controllers.projects.list`` for ``list`` function residing in ``app/controllers/projects.py`` file).
:paramref:`~.handlers.base.BaseRouteHandler.name` can be used to dynamically retrieve (i.e. during runtime) a mapping
containing the route handler instance and paths, also it can be used to build a URL path for that handler:

.. literalinclude:: /examples/routing/handler_indexing_1.py
    :caption: Using the :paramref:`~.handlers.base.BaseRouteHandler.name` :term:`kwarg <argument>` to retrieve a route
      handler instance and paths
    :language: python


:meth:`~.app.Litestar.route_reverse` will raise :exc:`~.exceptions.NoRouteMatchFoundException` if route with given
name was not found or if any of path :term:`parameters <parameter>` is missing or if any of passed path
:term:`parameters <parameter>` types do not match types in the respective route declaration.

However, :class:`str` is accepted in place of :class:`~datetime.datetime`, :class:`~datetime.date`,
:class:`~datetime.time`, :class:`~datetime.timedelta`, :class:`float`, and :class:`~pathlib.Path`
parameters, so you can apply custom formatting and pass the result to :meth:`~.app.Litestar.route_reverse`.

If handler has multiple paths attached to it :meth:`~.app.Litestar.route_reverse` will return the path that consumes
the most number of :term:`keyword arguments <argument>` passed to the function.

.. literalinclude:: /examples/routing/handler_indexing_2.py
    :caption: Using the :meth:`~.app.Litestar.route_reverse` method to build a URL path for a route handler
    :language: python


When a handler is associated with multiple routes having identical path :term:`parameters <parameter>`
(e.g., an indexed handler registered across multiple routers), the output of :meth:`~.app.Litestar.route_reverse` is
unpredictable. This :term:`callable` will return a formatted path; however, its selection may appear arbitrary.
Therefore, reversing URLs under these conditions is **strongly** advised against.

If you have access to :class:`~.connection.Request` instance you can make reverse lookups using
:meth:`~.connection.ASGIConnection.url_for` method which is similar to :meth:`~.app.Litestar.route_reverse` but
returns an absolute URL.

.. _handler_opts:

Adding arbitrary metadata to handlers
--------------------------------------

All route handler :term:`decorators <decorator>` accept a key called ``opt`` which accepts a :term:`dictionary <dict>`
of arbitrary values, e.g.,

.. literalinclude:: /examples/routing/handler_metadata_1.py
    :caption: Adding arbitrary metadata to a route handler through the ``opt`` :term:`kwarg <argument>`
    :language: python


This dictionary can be accessed by a :doc:`route guard </usage/security/guards>`, or by accessing the
:attr:`~.connection.ASGIConnection.route_handler` property on a :class:`~.connection.request.Request` object,
or using the :class:`ASGI scope <litestar.types.Scope>` object directly.

Building on ``opt``, you can pass any arbitrary :term:`kwarg <argument>` to the route handler :term:`decorator`,
and it will be automatically set as a key in the ``opt`` dictionary:

.. literalinclude:: /examples/routing/handler_metadata_2.py
    :caption: Adding arbitrary metadata to a route handler through the ``opt`` :term:`kwarg <argument>`
    :language: python


You can specify the ``opt`` :term:`dictionary <dict>` at all layers of your application.
On specific route handlers, on a controller, a router, and even on the app instance itself as described in
:ref:`layered architecture <usage/applications:layered architecture>`

The resulting :term:`dictionary <dict>` is constructed by merging ``opt`` dictionaries of all layers.
If multiple layers define the same key, the value from the closest layer to the response handler will take precedence.

.. _signature_namespace:

Signature :term:`namespace`
---------------------------

Litestar produces a model of the arguments to any handler or dependency function, called a "signature model" which is
used for parsing and validation of raw data to be injected into the function.

Building the model requires inspection of the names and types of the signature parameters at runtime, and so it is
necessary for the types to be available within the scope of the module - something that linting tools such as ``ruff``
or ``flake8-type-checking`` will actively monitor, and suggest against.

For example, the name ``Model`` is *not* available at runtime in the following snippet:

.. literalinclude:: /examples/signature_namespace/handler_signature_1.py
    :caption: A route handler with a type that is not available at runtime
    :language: python


In this example, Litestar will be unable to generate the signature model because the type ``Model`` does not exist in
the module scope at runtime. We can address this on a case-by-case basis by silencing our linters, for example:

.. literalinclude:: /examples/signature_namespace/handler_signature_2.py
    :no-upgrade:
    :caption: A Silencing linters for a type that is not available at runtime
    :language: python


However, this approach can get tedious; as an alternative, Litestar accepts a ``signature_types`` sequence at
every :ref:`layer <layered-architecture>` of the application, as demonstrated in the following example:

.. literalinclude:: /examples/signature_namespace/domain.py
    :caption: This module defines our domain type in some central place.

This module defines our controller, note that we do not import ``Model`` into the runtime :term:`namespace`,
nor do we require any directives to control behavior of linters.

.. literalinclude:: /examples/signature_namespace/controller.py
    :caption: This module defines our controller without importing ``Model`` into the runtime namespace.

Finally, we ensure that our application knows that when it encounters the name "Model" when parsing signatures, that it
should reference our domain ``Model`` type.

.. literalinclude:: /examples/signature_namespace/app.py
    :caption: Ensuring the application knows how to resolve the ``Model`` type when parsing signatures.

.. tip:: If you want to map your type to a name that is different from its ``__name__`` attribute,
    you can use the :paramref:`~.handlers.base.BaseRouteHandler.signature_namespace` parameter,
    e.g., ``app = Litestar(signature_namespace={"FooModel": Model})``.

    This enables import patterns like ``from domain.foo import Model as FooModel`` inside ``if TYPE_CHECKING`` blocks.

Default signature :term:`namespace`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Litestar automatically adds some names to the signature :term:`namespace` when parsing signature models in
order to support injection of the :ref:`handler-function-kwargs`.

These names are:

* ``Headers``
* ``ImmutableState``
* ``Receive``
* ``Request``
* ``Scope``
* ``Send``
* ``State``
* ``WebSocket``
* ``WebSocketScope``

The import of any of these names can be safely left inside an ``if TYPE_CHECKING:`` block without any configuration
required.
