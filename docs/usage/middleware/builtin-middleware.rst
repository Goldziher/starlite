Built-in middleware
===================

CORS
----

`CORS (Cross-Origin Resource Sharing) <https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS>`_ is a common security
mechanism that is often implemented using middleware. To enable CORS in a litestar application simply pass an instance
of :class:`CORSConfig <.config.cors.CORSConfig>` to :class:`Litestar <.app.Litestar>`:

.. code-block:: python

   from litestar import Litestar
   from litestar.config.cors import CORSConfig

   cors_config = CORSConfig(allow_origins=["https://www.example.com"])

   app = Litestar(route_handlers=[...], cors_config=cors_config)


CSRF
----

CSRF (Cross-site request forgery) is a type of attack where unauthorized commands are submitted from a user that the web
application trusts. This attack often uses social engineering that tricks the victim into clicking a URL that contains a
maliciously crafted, unauthorized request for a particular Web application. The user’s browser then sends this
maliciously crafted request to the targeted Web application. If the user is in an active session with the Web application,
the application treats this new request as an authorized request submitted by the user. Thus, the attacker can force the
user to perform an action the user didn't intend, for example:


.. code-block:: text

    POST /send-money HTTP/1.1
    Host: target.web.app
    Content-Type: application/x-www-form-urlencoded

    amount=1000usd&to=attacker@evil.com


This middleware prevents CSRF attacks by doing the following:

1. On the first "safe" request (e.g GET) - set a cookie with a special token created by the server
2. On each subsequent "unsafe" request (e.g POST) - make sure the request contains either a
    form field or an additional header that has this token (more on this below)

To enable CSRF protection in a Litestar application simply pass an instance of
:class:`CSRFConfig <.config.csrf.CSRFConfig>` to the Litestar constructor:

.. code-block:: python

    from litestar import Litestar, get, post
    from litestar.config.csrf import CSRFConfig


    @get()
    async def get_resource() -> str:
        # GET is one of the safe methods
        return "some_resource"

    @post("{id:int}")
    async def create_resource(id: int) -> bool:
        # POST is one of the unsafe methods
        return True

    csrf_config = CSRFConfig(secret="my-secret")

    app = Litestar([get_resource, create_resource], csrf_config=csrf_config)


The following snippet demonstrates how to change the cookie name to "some-cookie-name" and header name to "some-header-name".

.. code-block:: python

    csrf_config = CSRFConfig(secret="my-secret", cookie_name='some-cookie-name', header_name='some-header-name')


A CSRF protected route can be accessed by any client that can make a request with either the header or form-data key.


.. note::

    The form-data key can not be currently configured. It should only be passed via the key "_csrf_token"

In Python, any client such as `requests <https://github.com/psf/requests>`_ or `httpx <https://github.com/encode/httpx>`_ can be used.
The usage of clients or sessions is recommended due to the cookie persistence it offers across requests.
The following is an example using ``httpx.Client``.

.. code-block:: python

    import httpx


    with httpx.Client() as client:
        get_response = client.get("http://localhost:8000/")

        # "csrftoken" is the default cookie name
        csrf = get_response.cookies["csrftoken"]

        # "x-csrftoken" is the default header name
        post_response_using_header = client.post("http://localhost:8000/", headers={"x-csrftoken": csrf})
        assert post_response_using_header.status_code == 201

        # "_csrf_token" is the default *non* configurable form-data key
        post_response_using_form_data = client.post("http://localhost:8000/1", data={"_csrf_token": csrf})
        assert post_response_using_form_data.status_code == 201

        # despite the header being passed, this request will fail as it does not have a cookie in its session
        # note the usage of ``httpx.post`` instead of ``client.post``
        post_response_with_no_persisted_cookie = httpx.post("http://localhost:8000/1", headers={"x-csrftoken": csrf})
        assert post_response_with_no_persisted_cookie.status_code == 403
        assert "CSRF token verification failed" in post_response_with_no_persisted_cookie.text

Routes can be marked as being exempt from the protection offered by this middleware via
:ref:`handler opts <handler_opts>`

.. code-block:: python

    @post("/post", exclude_from_csrf=True)
    def handler() -> None: ...


If you need to exempt many routes at once you might want to consider using the
:attr:`exclude <.config.csrf.CSRFConfig.exclude>` kwarg which accepts list of path
patterns to skip in the middleware.

.. seealso::

    * `Safe and Unsafe (HTTP Methods) <https://developer.mozilla.org/en-US/docs/Glossary/Safe/HTTP>`_
    * `HTTPX Clients <https://www.python-httpx.org/advanced/clients>`_
    * `Requests Session <https://requests.readthedocs.io/en/latest/user/advanced>`_


Allowed Hosts
-------------

Another common security mechanism is to require that each incoming request has a "Host" or "X-Forwarded-Host" header,
and then to restrict hosts to a specific set of domains - what's called "allowed hosts".

Litestar includes an :class:`AllowedHostsMiddleware <.middleware.allowed_hosts.AllowedHostsMiddleware>` class that can be
easily enabled by either passing an instance of :class:`AllowedHostsConfig <.config.allowed_hosts.AllowedHostsConfig>` or a
list of domains to :class:`Litestar <litestar.app.Litestar>`:

.. code-block:: python

   from litestar import Litestar
   from litestar.config.allowed_hosts import AllowedHostsConfig

   app = Litestar(
       route_handlers=[...],
       allowed_hosts=AllowedHostsConfig(
           allowed_hosts=["*.example.com", "www.wikipedia.org"]
       ),
   )

.. note::

    You can use wildcard prefixes (``*.``) in the beginning of a domain to match any combination of subdomains. Thus,
    ``*.example.com`` will match ``www.example.com`` but also ``x.y.z.example.com`` etc. You can also simply put ``*``
    in trusted hosts, which means allow all. This is akin to turning the middleware off, so in this case it may be
    better to not enable it in the first place. You should note that a wildcard can only be used only in the prefix of a
    domain name, not in the middle or end. Doing so will result in a validation exception being raised.


Compression
-----------

HTML responses can optionally be compressed. Litestar has built in support for gzip and brotli. Gzip support is provided
through the built-in Starlette classes, and brotli support can be added by installing the ``brotli`` extras.

You can enable either backend by passing an instance of
:class:`CompressionConfig <.config.compression.CompressionConfig>` to ``compression_config`` of
:class:`Litestar <litestar.app.Litestar>`.

GZIP
^^^^

You can enable gzip compression of responses by passing an instance of :class:`CompressionConfig <.config.compression.CompressionConfig>` with
the ``backend`` parameter set to ``"gzip"``.

You can configure the following additional gzip-specific values:


* ``minimum_size``: the minimum threshold for response size to enable compression. Smaller responses will not be
    compressed. Defaults is ``500``, i.e. half a kilobyte.
* ``gzip_compress_level``: a range between 0-9, see the `official python docs <https://docs.python.org/3/library/gzip.html>`_.
    Defaults to ``9`` , which is the maximum value.

.. code-block:: python

   from litestar import Litestar
   from litestar.config.compression import CompressionConfig

   app = Litestar(
       route_handlers=[...],
       compression_config=CompressionConfig(backend="gzip", gzip_compress_level=9),
   )

Brotli
^^^^^^

The Brotli package is required to run this middleware. It is available as an extras to litestar with the ``brotli``
extra (``pip install litestar[brotli]``).

You can enable brotli compression of responses by passing an instance of
:class:`CompressionConfig <.config.compression.CompressionConfig>` with the ``backend`` parameter set to ``"brotli"``.

You can configure the following additional brotli-specific values:


* ``minimum_size``: the minimum threshold for response size to enable compression. Smaller responses will not be
    compressed. Defaults is ``500``, i.e. half a kilobyte.
* ``brotli_quality``: Range [0-11], Controls the compression-speed vs compression-density tradeoff. The higher the
    quality, the slower the compression.
* ``brotli_mode``: The compression mode can be MODE_GENERIC (default), MODE_TEXT (for UTF-8 format text input), or
    MODE_FONT (for WOFF 2.0).
* ``brotli_lgwin``: Base 2 logarithm of size. Range is 10 to 24. Defaults to 22.
* ``brotli_lgblock``: Base 2 logarithm of the maximum input block size. Range is 16 to 24. If set to 0, the value will
    be set based on the quality. Defaults to 0.
* ``brotli_gzip_fallback``: a boolean to indicate if gzip should be used if brotli is not supported.

.. code-block:: python

   from litestar import Litestar
   from litestar.config.compression import CompressionConfig

   app = Litestar(
       route_handlers=[...],
       compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=True),
   )

Rate-Limit Middleware
---------------------

Litestar includes an optional :class:`RateLimitMiddleware <litestar.middleware.rate_limit.RateLimitMiddleware>` that follows
the `IETF RateLimit draft specification <https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/>`_.

To use the rate limit middleware, use the :class:`RateLimitConfig <litestar.middleware.rate_limit.RateLimitConfig>`:

.. literalinclude:: /examples/middleware/rate_limit.py
    :language: python

The only required configuration kwarg is ``rate_limit``, which expects a tuple containing a time-unit (``second``,
``minute``, ``hour``, ``day``\ ) and a value for the request quota (integer).


Logging Middleware
------------------

Litestar ships with a robust logging middleware that allows logging HTTP request and responses while building on
the :doc:`logging configuration </usage/logging>`:

.. literalinclude:: /examples/middleware/logging_middleware.py
    :language: python


The logging middleware uses the logger configuration defined on the application level, which allows for using both stdlib
logging or `structlog <https://www.structlog.org/en/stable/index.html>`_ , depending on the configuration used
(see :doc:`logging configuration </usage/logging>` for more details).

Obfuscating Logging Output
^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes certain data, e.g. request or response headers, needs to be obfuscated. This is supported by the middleware
configuration:

.. code-block:: python

   from litestar.middleware.logging import LoggingMiddlewareConfig

   logging_middleware_config = LoggingMiddlewareConfig(
       request_cookies_to_obfuscate={"my-custom-session-key"},
       response_cookies_to_obfuscate={"my-custom-session-key"},
       request_headers_to_obfuscate={"my-custom-header"},
       response_headers_to_obfuscate={"my-custom-header"},
   )

The middleware will obfuscate the headers ``Authorization`` and ``X-API-KEY`` , and the cookie ``session`` by default.


Compression and Logging of Response Body
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If both :class:`CompressionConfig <litestar.config.compression.CompressionConfig>` and
:class:`LoggingMiddleware <litestar.middleware.logging.LoggingMiddleware>` have been defined for the application, the response
body will be omitted from response logging if it has been compressed, even if ``"body"`` has been included in
:class:`response_log_fields <litestar.middleware.logging.LoggingMiddlewareConfig.response_log_fields>`. To force the body of
compressed responses to be logged, set
:attr:`include_compressed_body <litestar.middleware.logging.LoggingMiddlewareConfig.include_compressed_body>` to ``True`` , in
addition to including ``"body"`` in ``response_log_fields``.

Session Middleware
------------------

Litestar includes a :class:`SessionMiddleware <.middleware.session.base.SessionMiddleware>`,
offering client- and server-side sessions. Server-side sessions are backed by Litestar's
:doc:`stores </usage/stores>`, which offer support for:

- In memory sessions
- File based sessions
- Redis based sessions

Setting up the middleware
^^^^^^^^^^^^^^^^^^^^^^^^^

To start using sessions in your application all you have to do is create an instance
of a :class:`configuration <litestar.middleware.session.base.BaseBackendConfig>` object and
add its middleware to your application's middleware stack:

.. literalinclude:: /examples/middleware/session/cookies_full_example.py
    :caption: Hello World
    :language: python


.. note::

    Since both client- and server-side sessions rely on cookies (one for storing the actual session
    data, the other for storing the session ID), they share most of the cookie configuration.
    A complete reference of the cookie configuration can be found at :class:`BaseBackendConfig <litestar.middleware.session.base.BaseBackendConfig>`.

Client-side sessions
^^^^^^^^^^^^^^^^^^^^

Client side sessions are available through the :class:`ClientSideSessionBackend <litestar.middleware.session.client_side.ClientSideSessionBackend>`,
which offers strong AES-CGM encryption security best practices while support cookie splitting.

.. important::

    ``ClientSideSessionBackend`` requires the `cryptography <https://cryptography.io/en/latest/>`_ library,
    which can be installed together with litestar as an extra using ``pip install litestar[cryptography]``

.. literalinclude:: /examples/middleware/session/cookie_backend.py
    :caption: cookie_backend.py
    :language: python


.. seealso::

    * :class:`CookieBackendConfig <litestar.middleware.session.client_side.CookieBackendConfig>`


Server-side sessions
^^^^^^^^^^^^^^^^^^^^

Server side session store data - as the name suggests - on the server instead of the client.
They use a cookie containing a session ID which is a randomly generated string to identify a client
and load the appropriate data from the store

.. literalinclude:: /examples/middleware/session/file_store.py


.. seealso::

    * :doc:`/usage/stores`
    * :class:`ServerSideSessionConfig <litestar.middleware.session.server_side.ServerSideSessionConfig>`
