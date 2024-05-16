From Starlette / FastAPI
------------------------

Routing Decorators
~~~~~~~~~~~~~~~~~~

Litestar does not include any decorator as part of the ``Router`` or ``Litestar`` instances.
Instead, all routes are declared using :doc:`route handlers </usage/routing/handlers>`, either as standalone functions or
controller methods. The handler can then be registered on an application or router instance.

.. tab-set::

    .. tab-item:: FastAPI
        :sync: fastapi

        .. literalinclude:: /examples/migrations/fastapi/routing_fastapi.py
            :language: python


    .. tab-item:: Starlette
        :sync: starlette

        .. literalinclude:: /examples/migrations/fastapi/routing_starlette.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/fastapi/routing_litestar.py
            :language: python

..  seealso::

    To learn more about registering routes, check out this chapter
    in the documentation:

    * :ref:`Routing - Registering Routes <usage/routing/overview:registering routes>`

Routers and Routes
~~~~~~~~~~~~~~~~~~

There are a few key differences between Litestar’s and Starlette’s ``Router`` class:

1. The Litestar version is not an ASGI app
2. The Litestar version does not include decorators: Use :doc:`route handlers </usage/routing/handlers>`.
3. The Litestar version does not support lifecycle hooks: Those have to be handled on the application layer. See :doc:`lifecycle hooks </usage/lifecycle-hooks>`

If you are using Starlette’s ``Route``\ s, you will need to replace these with :doc:`route handlers </usage/routing/handlers>`.

Host based routing
~~~~~~~~~~~~~~~~~~

Host based routing class is intentionally unsupported. If your application relies on ``Host`` you will have to separate
the logic into different services and handle this part of request dispatching with a proxy server like `nginx <https://www.nginx.com/>`_
or `traefik <https://traefik.io/>`_.

Dependency Injection
~~~~~~~~~~~~~~~~~~~~

The Litestar dependency injection system is different from the one used by FastAPI. You can read about it in
the :doc:`dependency injection </usage/dependency-injection>` section of the documentation.

In FastAPI you declare dependencies either as a list of functions passed to the ``Router`` or ``FastAPI`` instances, or as a
default function argument value wrapped in an instance of the ``Depends`` class.

In Litestar **dependencies are always declared using a dictionary** with a string key and the value wrapped in an
instance of the ``Provide`` class. This also allows to transparently override dependencies on every level of the application,
and to easily access dependencies from higher levels.

.. tab-set::

    .. tab-item:: FastAPI
        :sync: fastapi

        .. literalinclude:: /examples/migrations/fastapi/di_fastapi.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/fastapi/di_litestar.py
            :language: python


..  seealso::

    To learn more about dependency injection, check out this chapter
    in the documentation:

    * :doc:`/usage/dependency-injection`

Authentication
^^^^^^^^^^^^^^

FastAPI promotes a pattern of using dependency injection for authentication. You can do the same in Litestar, but the
preferred way of handling this is extending :doc:`/usage/security/abstract-authentication-middleware`.

.. tab-set::
    .. tab-item:: FastAPI
        :sync: fastapi

        .. literalinclude:: /examples/migrations/fastapi/authentication_fastapi.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/fastapi/authentication_litestar.py
            :language: python


..  seealso::

    To learn more about security and authentication, check out this chapter in the
    documentation:

    * :doc:`/usage/security/index`

Dependency overrides
^^^^^^^^^^^^^^^^^^^^

While FastAPI includes a mechanism to override dependencies on an existing application object,
Litestar promotes architectural solutions to the issue this is aimed to solve. Therefore, overriding
dependencies in Litestar is strictly supported at definition time, i.e. when you’re defining
handlers, controllers, routers, and applications. Dependency overrides are fundamentally
the same idea as mocking and should be approached with the same caution and used sparingly
instead of being the default.

To achieve the same effect there are three general approaches:

1. Structuring the application with different environments in mind. This could mean for example
   connecting to a different database depending on the environment, which in turn is set via
   and env-variable. This is sufficient and most cases and designing your application around this
   principle is a general good practice since it facilitates configurability and integration-testing
   capabilities
2. Isolating tests for unit testing and using ``create_test_client``
3. Resort to mocking if none of the above approaches can be made to work

Middleware
~~~~~~~~~~

Pure ASGI middleware is fully compatible, and can be used with any ASGI framework. Middlewares
that make use of FastAPI/Starlette specific middleware features such as
Starlette’s `BaseHTTPMiddleware <https://www.starlette.io/middleware/#basehttpmiddleware>`_ are not compatible,
but can be easily replaced by :doc:`Creating Middlewares </usage/middleware/creating-middleware>`.
