From Flask
----------

ASGI vs WSGI
~~~~~~~~~~~~

`Flask <https://flask.palletsprojects.com>`_ is a WSGI framework, whereas Litestar
is built using the modern `ASGI <https://asgi.readthedocs.io>`_ standard. A key difference
is that *ASGI* is built with async in mind.

While Flask has added support for ``async/await``, it remains synchronous at its core;
The async support in Flask is limited to individual endpoints.
What this means is that while you can use ``async def`` to define endpoints in Flask,
**they will not run concurrently** - requests will still be processed one at a time.
Flask handles asynchronous endpoints by creating an event loop for each request, run the
endpoint function in it, and then return its result.

ASGI on the other hand does the exact opposite; It runs everything in a central event loop.
Litestar then adds support for synchronous functions by running them in a non-blocking way
*on the event loop*. What this means is that synchronous and asynchronous code both run
concurrently.

Routing
~~~~~~~

.. tab-set::

    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/routing_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/routing_litestar.py
            :language: python


Path parameters
^^^^^^^^^^^^^^^

.. tab-set::
    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/path_parameters_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/path_parameters_litestar.py
            :language: python


..  seealso::

    To learn more about path parameters, check out this chapter
    in the documentation:

    * :doc:`/usage/routing/parameters`

Request object
~~~~~~~~~~~~~~

In Flask, the current request can be accessed through a global ``request`` variable. In Litestar,
the request can be accessed through an optional parameter in the handler function.

.. tab-set::

    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/request_object_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/request_object_litestar.py
            :language: python


Request methods
^^^^^^^^^^^^^^^

+---------------------------------+-------------------------------------------------------------------------------------------------------+
| Flask                           | Litestar                                                                                              |
+=================================+=======================================================================================================+
| ``request.args``                | ``request.query_params``                                                                              |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.base_url``            | ``request.base_url``                                                                                  |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.authorization``       | ``request.auth``                                                                                      |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.cache_control``       | ``request.headers.get("cache-control")``                                                              |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.content_encoding``    | ``request.headers.get("content-encoding")``                                                           |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.content_length``      | ``request.headers.get("content-length")``                                                             |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.content_md5``         | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.content_type``        | ``request.content_type``                                                                              |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.cookies``             | ``request.cookies``                                                                                   |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.data``                | ``request.body()``                                                                                    |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.date``                | ``request.headers.get("date")``                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.endpoint``            | ``request.route_handler``                                                                             |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.environ``             | ``request.scope``                                                                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.files``               | Use ```UploadFile`` <usage/4-request-data/#file-uploads>`__                                           |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.form``                | ``request.form()``, prefer ```Body`` <usage/4-request-data/#specifying-a-content-type>`__             |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.get_json``            | ``request.json()``, prefer the ```data keyword argument`` <usage/4-request-data/#request-body>`__     |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.headers``             | ``request.headers``                                                                                   |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.host``                | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.host_url``            | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.if_match``            | ``request.headers.get("if-match")``                                                                   |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.if_modified_since``   | ``request.headers.get("if_modified_since")``                                                          |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.if_none_match``       | ``request.headers.get("if_none_match")``                                                              |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.if_range``            | ``request.headers.get("if_range")``                                                                   |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.if_unmodified_since`` | ``request.headers.get("if_unmodified_since")``                                                        |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.method``              | ``request.method``                                                                                    |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.mimetype``            | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.mimetype_params``     | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.origin``              | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.path``                | ``request.scope["path"]``                                                                             |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.query_string``        | ``request.scope["query_string"]``                                                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.range``               | ``request.headers.get("range")``                                                                      |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.referrer``            | ``request.headers.get("referrer")``                                                                   |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.remote_addr``         | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.remote_user``         | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.root_path``           | ``request.scope["root_path"]``                                                                        |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.server``              | ``request.scope["server"]``                                                                           |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.stream``              | ``request.stream``                                                                                    |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.url``                 | ``request.url``                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.url_charset``         | :octicon:`dash`                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.user_agent``          | ``request.headers.get("user-agent")``                                                                 |
+---------------------------------+-------------------------------------------------------------------------------------------------------+
| ``request.user_agent``          | ``request.headers.get("user-agent")``                                                                 |
+---------------------------------+-------------------------------------------------------------------------------------------------------+

..  seealso::

    To learn more about requests, check out these chapters in the documentation

    * :doc:`/usage/requests`
    * :doc:`/reference/connection`

Static files
~~~~~~~~~~~~

Like Flask, Litestar also has capabilities for serving static files, but while Flask
will automatically serve files from a ``static`` folder, this has to be configured explicitly
in Litestar.

.. literalinclude:: /examples/migrations/flask/static_files.py
    :language: python


..  seealso::

    To learn more about static files, check out this chapter in the documentation

    * :doc:`/usage/static-files`

Templates
~~~~~~~~~

Flask comes with the `Jinja <https://jinja.palletsprojects.com/en/3.1.x/>`_ templating
engine built-in. You can use Jinja with Litestar as well, but you’ll need to install it
explicitly. You can do by installing Litestar with ``pip install litestar[jinja]``.
In addition to Jinja, Litestar supports `Mako <https://www.makotemplates.org/>`_ and `Minijinja <https://github.com/mitsuhiko/minijinja/tree/main/minijinja-py>`_ templates as well.

.. tab-set::
    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/templates_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/templates_litestar.py
            :language: python


..  seealso::
    To learn more about templates, check out this chapter in the documentation:

    * :doc:`/usage/templating`

Setting cookies and headers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/cookies_headers_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/cookies_headers_litestar.py
            :language: python


..  seealso::
    To learn more about response headers and cookies, check out these chapters in the
    documentation:

    - :ref:`Responses - Setting Response Headers <usage/responses:setting response headers>`
    - :ref:`Responses - Setting Response Cookies <usage/responses:setting response cookies>`

Redirects
~~~~~~~~~

For redirects, instead of ``redirect`` use ``Redirect``:

.. tab-set::

    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/redirects_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/redirects_litestar.py
            :language: python


Raising HTTP errors
~~~~~~~~~~~~~~~~~~~

Instead of using the ``abort`` function, raise an ``HTTPException``:

.. tab-set::

    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/errors_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/errors_litestar.py
            :language: python


..  seealso::
    To learn more about exceptions, check out this chapter in the documentation:

    * :doc:`/usage/exceptions`

Setting status codes
~~~~~~~~~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/status_codes_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/status_codes_litestar.py
            :language: python


Serialization
~~~~~~~~~~~~~

Flask uses a mix of explicit conversion (such as ``jsonify``) and inference (i.e. the type
of the returned data) to determine how data should be serialized. Litestar instead assumes
the data returned is intended to be serialized into JSON and will do so unless told otherwise.

.. tab-set::

    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/serialization_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/serialization_litestar.py
            :language: python


Error handling
~~~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Flask
        :sync: flask

        .. literalinclude:: /examples/migrations/flask/error_handling_flask.py
            :language: python


    .. tab-item:: Litestar
        :sync: litestar

        .. literalinclude:: /examples/migrations/flask/error_handling_litestar.py
            :language: python


..  seealso::

    To learn more about exception handling, check out this chapter in the documentation:

    * :ref:`usage/exceptions:exception handling`
