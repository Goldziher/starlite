==================================
Implementing Custom Authentication
==================================

Litestar exports :class:`~.middleware.authentication.AbstractAuthenticationMiddleware`, which is an
:term:`abstract base class` (ABC) that implements the :class:`~.middleware.base.MiddlewareProtocol`.
To add authentication to your app using this class as a basis, subclass it and implement the abstract method
:meth:`~.middleware.authentication.AbstractAuthenticationMiddleware.authenticate_request`:

.. literalinclude:: /examples/security/middleware/auth_middleware_1.py
    :caption: Adding authentication to your app by subclassing
      :class:`~.middleware.authentication.AbstractAuthenticationMiddleware`
    :language: python


As you can see, ``authenticate_request`` is an async function that receives a connection instance and is supposed to return
an :class:`~.middleware.authentication.AuthenticationResult` instance, which is a
:doc:`dataclass <python:library/dataclasses>` that has two attributes:

1. ``user``: a non-optional value representing a user. It is typed as ``Any`` so it receives any value,
   including ``None``.
2. ``auth``: an optional value representing the authentication scheme. Defaults to ``None``.

These values are then set as part of the ``scope`` dictionary, and they are made available as
:attr:`Request.user <.connection.ASGIConnection.user>`
and :attr:`Request.auth <.connection.ASGIConnection.auth>` respectively, for HTTP route handlers, and
:attr:`WebSocket.user <.connection.ASGIConnection.user>` and
:attr:`WebSocket.auth <.connection.ASGIConnection.auth>` for websocket route handlers.

Creating a Custom JWT Authentication Middleware
-----------------------------------------------

Since the above is quite hard to grasp in the abstract, let us see an example.

We start off by creating a user model. It can be implemented using Pydantic, an ODM, ORM, etc. For the sake of the
example here let us say it is a `SQLAlchemy <https://docs.sqlalchemy.org/>`_ model:

.. literalinclude:: /examples/security/middleware/auth_middleware_model.py
    :caption: my_app/db/models.py
    :language: python


We will also need some utility methods to encode and decode tokens. To this end we will use
the `python-jose <https://github.com/mpdavis/python-jose>`_ library. We will also create a Pydantic model representing a
JWT Token:

.. dropdown:: Click to see the JWT utility methods and Token model

    .. literalinclude:: /examples/security/middleware/auth_middleware_jwt.py
        :caption: my_app/security/jwt.py
        :language: python


We can now create our authentication middleware:

.. literalinclude:: /examples/security/middleware/auth_middleware_creation.py
    :caption: my_app/security/authentication_middleware_cr.py
    :language: python


Finally, we need to pass our middleware to the Litestar constructor:

.. literalinclude:: /examples/security/middleware/auth_middleware_to_app.py
    :caption: my_app/main.py
    :language: python


That is it. The ``JWTAuthenticationMiddleware`` will now run for every request, and we would be able to access these in a
http route handler in the following way:

.. literalinclude:: /examples/security/middleware/auth_middleware_route.py
    :caption: Accessing the user and auth in a route handler with the JWTAuthenticationMiddleware
    :language: python


Or for a websocket route:

.. literalinclude:: /examples/security/middleware/auth_middleware_websocket.py
    :caption: Accessing the user and auth in a websocket route handler with the JWTAuthenticationMiddleware
    :language: python


And if you would like to exclude individual routes outside those configured:

.. dropdown:: Click to see how to exclude individual routes from the JWTAuthenticationMiddleware

.. literalinclude:: /examples/security/middleware/auth_middleware_exclude_route.py
    :caption: Excluding individual routes from the JWTAuthenticationMiddleware
    :language: python


And of course use the same kind of mechanism for dependencies:

.. literalinclude:: /examples/security/middleware/auth_middleware_dependencies.py
    :caption: Using the JWTAuthenticationMiddleware in a dependency
    :language: python
