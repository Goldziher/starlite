
Creating Middleware
===================

As mentioned in :doc:`using middleware </usage/middleware/using-middleware>`, a middleware in Litestar
is **any callable** that takes a kwarg called ``app``, which is the next ASGI handler, i.e. an
:class:`ASGIApp <litestar.types.ASGIApp>`, and returns an ``ASGIApp``.

The example previously given was using a factory function, i.e.:

.. literalinclude:: /examples/middleware/creation/create_basic_middleware.py
    :language: python

While using functions is a perfectly viable approach, you can also use classes to do the same. See the next sections on
two base classes you can use for this purpose - the :class:`MiddlewareProtocol <.middleware.base.MiddlewareProtocol>` ,
which gives a bare-bones type, or the :class:`AbstractMiddleware <.middleware.base.AbstractMiddleware>` that offers a
base class with some built in functionality.

Using MiddlewareProtocol
------------------------

The :class:`MiddlewareProtocol <litestar.middleware.base.MiddlewareProtocol>` class is a
`PEP 544 Protocol <https://peps.python.org/pep-0544/>`_ that specifies the minimal implementation of a middleware as
follows:

.. literalinclude:: /examples/middleware/creation/create_middleware_using_middleware_protocol_1.py
    :language: python


The ``__init__`` method receives and sets "app". *It's important to understand* that app is not an instance of Litestar in
this case, but rather the next middleware in the stack, which is also an ASGI app.

The ``__call__`` method makes this class into a ``callable``, i.e. once instantiated this class acts like a function, that
has the signature of an ASGI app: The three parameters, ``scope, receive, send`` are specified
by `the ASGI specification <https://asgi.readthedocs.io/en/latest/index.html>`_, and their values originate with the ASGI
server (e.g. *uvicorn*\ ) used to run Litestar.

To use this protocol as a basis, simply subclass it - as you would any other class, and implement the two methods it
specifies:

.. literalinclude:: /examples/middleware/creation/create_middleware_using_middleware_protocol_2.py
    :language: python


.. important::

    Although ``scope`` is used to create an instance of request by passing it to the
    :class:`Request <.connection.Request>` constructor, which makes it simpler to access because it does some parsing
    for you already, the actual source of truth remains ``scope`` - not the request. If you need to modify the data of
    the request you must modify the scope object, not any ephemeral request objects created as in the above.


Responding using the MiddlewareProtocol
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once a middleware finishes doing whatever its doing, it should pass ``scope``, ``receive``, and ``send`` to an ASGI app
and await it. This is what's happening in the above example with: ``await self.app(scope, receive, send)``. Let's
explore another example - redirecting the request to a different url from a middleware:

.. literalinclude:: /examples/middleware/creation/responding_using_middleware_protocol.py
    :language: python


As you can see in the above, given some condition (``request.session`` being None) we create a
:class:`ASGIRedirectResponse <litestar.response.redirect.ASGIRedirectResponse>` and then await it. Otherwise, we await ``self.app``

Modifying ASGI Requests and Responses using the MiddlewareProtocol
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. important::

    If you'd like to modify a :class:`Response <.response.Response>` object after it was created for a route
    handler function but before the actual response message is transmitted, the correct place to do this is using the
    special life-cycle hook called :ref:`after_request <after_request>`. The instructions in this section are for how to
    modify the ASGI response message itself, which is a step further in the response process.

Using the :class:`MiddlewareProtocol <.middleware.base.MiddlewareProtocol>` you can intercept and modifying both the
incoming and outgoing data in a request / response cycle by "wrapping" that respective ``receive`` and ``send`` ASGI
functions.

To demonstrate this, lets say we want to append a header with a timestamp to all outgoing responses. We could achieve
this by doing the following:

.. literalinclude:: /examples/middleware/creation/responding_using_middleware_protocol_asgi.py
    :language: python


Inheriting AbstractMiddleware
-----------------------------

Litestar offers an :class:`AbstractMiddleware <.middleware.base.AbstractMiddleware>` class that can be extended to
create middleware:

.. literalinclude:: /examples/middleware/creation/inheriting_abstract_middleware.py
    :language: python


The three class variables defined in the above example ``scopes``, ``exclude``, and ``exclude_opt_key`` can be used to
fine-tune for which routes and request types the middleware is called:


- The scopes variable is a set that can include either or both ``ScopeType.HTTP`` and ``ScopeType.WEBSOCKET`` , with the default being both.
- ``exclude`` accepts either a single string or list of strings that are compiled into a regex against which the request's ``path`` is checked.
- ``exclude_opt_key`` is the key to use for in a route handler's ``opt`` dict for a boolean, whether to omit from the middleware.

Thus, in the following example, the middleware will only run against the route handler called ``not_excluded_handler``:

.. literalinclude:: /examples/middleware/base.py
    :language: python


Using DefineMiddleware to pass arguments
----------------------------------------

Litestar offers a simple way to pass positional arguments (``*args``) and key-word arguments (``**kwargs``) to middleware
using the :class:`DefineMiddleware <litestar.middleware.base.DefineMiddleware>` class. Let's extend
the factory function used in the examples above to take some args and kwargs and then use ``DefineMiddleware`` to pass
these values to our middleware:

.. literalinclude:: /examples/middleware/creation/using_define_middleware.py
    :language: python


The ``DefineMiddleware`` is a simple container - it takes a middleware callable as a first parameter, and then any
positional arguments, followed by key word arguments. The middleware callable will be called with these values as well
as the kwarg ``app`` as mentioned above.
