Excluding and including endpoints
=================================

Please make sure you read the :doc:`security backends documentation </usage/security/security-backends>` first for learning how to set up a security backend. This section focuses on configuring the ``exclude`` rule for those backends.

There are multiple ways for including or excluding endpoints in the authentication flow. The default rules are configured in the ``Auth`` object used (subclass of :class:`~.security.base.AbstractSecurityConfig`). The examples below use :class:`~.security.session_auth.auth.SessionAuth` but it is the same for :class:`~.security.jwt.auth.JWTAuth` and :class:`~.security.jwt.auth.JWTCookieAuth`.

Excluding routes
--------------------

The ``exclude`` argument takes a :class:`string <str>` or :class:`list` of :class:`strings <str>` that are interpreted as regex patterns. For example, the configuration below would apply authentication to all endpoints except those where the route starts with ``/login``, ``/signup``, or ``/schema``. Thus, one does not have to exclude ``/schema/swagger`` as well - it is included in the ``/schema`` pattern.

This also means that passing ``/`` will disable authentication for all routes.

.. code-block:: python

    session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,
    # we must pass a config for a session backend.
    # all session backends are supported
    session_backend_config=ServerSideSessionConfig(),
    # exclude any URLs that should not have authentication.
    # We exclude the documentation URLs, signup and login.
    exclude=["/login", "/signup", "/schema"],
    )
    ...

Including routes
----------------

Since the exclusion rules are evaluated as regex, it is possible to pass a rule that inverts exclusion - meaning, no path but the one specified in the pattern will be protected by authentication. In the example below, only endpoints under the ``/secured`` route will require authentication - all other routes do not.

.. code-block:: python

    ...
    session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,
    # we must pass a config for a session backend.
    # all session backends are supported
    session_backend_config=ServerSideSessionConfig(),
    # exclude any URLs that should not have authentication.
    # We exclude the documentation URLs, signup and login.
    exclude=[r"^(?!.*\/secured$).*$"],
    )
    ...

Exclude from auth
--------------------
Sometimes, you might want to apply authentication to all endpoints under a route but a few selected. In this case, you can pass ``exclude_from_auth=True`` to the route handler as shown below.

.. code-block:: python

    ...
    @get("/secured")
    def secured_route() -> Any:
        ...

    @get("/unsecured", exclude_from_auth=True)
    def unsecured_route() -> Any:
        ...
    ...

You can set an alternative option key in the security configuration, e.g., you can use ``no_auth`` instead of ``exclude_from_auth``.

.. code-block:: python

    ...
    @get("/secured")
    def secured_route() -> Any:
        ...

    @get("/unsecured", no_auth=True)
    def unsecured_route() -> Any:
        ...

    session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,
    # we must pass a config for a session backend.
    # all session backends are supported
    session_backend_config=ServerSideSessionConfig(),
    # exclude any URLs that should not have authentication.
    # We exclude the documentation URLs, signup and login.
    exclude=["/login", "/signup", "/schema"],
    exclude_opt_key="no_auth"  # default value is `exclude_from_auth`
    )
    ...
