Testing
=======

Testing is a first class citizen in Litestar, which offers several powerful testing utilities out of the box.


Test Client
-----------

Litestar's test client is built on top of
the `httpx <https://github.com/encode/httpx>`_ library. To use the test client you should pass to it an
instance of Litestar as the ``app`` kwarg.

Let's say we have a very simple app with a health check endpoint:

.. literalinclude:: /examples/testing/test_client_base.py
    :caption: my_app/main.py
    :language: python


We would then test it using the test client like so:

.. tab-set::

    .. tab-item:: Sync
        :sync: sync

        .. literalinclude:: /examples/testing/test_client_sync.py
            :caption: tests/test_health_check.py
            :language: python


    .. tab-item:: Async
        :sync: async

        .. literalinclude:: /examples/testing/test_client_async.py
            :caption: tests/test_health_check.py
            :language: python


Since we would probably need to use the client in multiple places, it's better to make it into a pytest fixture:


.. tab-set::

    .. tab-item:: Sync
        :sync: sync

        .. literalinclude:: /examples/testing/test_client_conf_sync.py
            :caption: tests/conftest.py
            :language: python


    .. tab-item:: Async
        :sync: async

        .. literalinclude:: /examples/testing/test_client_conf_async.py
            :caption: tests/conftest.py
            :language: python



We would then be able to rewrite our test like so:

.. tab-set::

    .. tab-item:: Sync
        :sync: sync

        .. literalinclude:: /examples/testing/test_health_check_sync.py
            :caption: tests/test_health_check.py
            :language: python


    .. tab-item:: Async
        :sync: async

        .. literalinclude:: /examples/testing/test_health_check_async.py
            :caption: tests/test_health_check.py
            :language: python


Using sessions
++++++++++++++

If you are using :ref:`session middleware <usage/middleware/builtin-middleware:session middleware>` for session persistence
across requests, then you might want to inject or inspect session data outside a request. For this,
:class:`TestClient <.testing.TestClient>` provides two methods:

* :meth:`set_session_data <litestar.testing.TestClient.set_session_data>`
* :meth:`get_session_data <litestar.testing.TestClient.get_session_data>`

.. attention::

    - The Session Middleware must be enabled in Litestar app provided to the TestClient to use sessions.
    - If you are using the
      :class:`ClientSideSessionBackend <litestar.middleware.session.client_side.ClientSideSessionBackend>` you need to
      install the ``cryptography`` package. You can do so by installing ``litestar``:

    .. tab-set::

        .. tab-item:: pip

            .. code-block:: bash
                :caption: Using pip

                python3 -m pip install litestar[cryptography]

        .. tab-item:: pipx

            .. code-block:: bash
                :caption: Using `pipx <https://pypa.github.io/pipx/>`_

                pipx install litestar[cryptography]

        .. tab-item:: pdm

            .. code-block:: bash
                :caption: Using `PDM <https://pdm.fming.dev/>`_

                pdm add litestar[cryptography]

        .. tab-item:: Poetry

            .. code-block:: bash
                :caption: Using `Poetry <https://python-poetry.org/>`_

                poetry add litestar[cryptography]

.. tab-set::

    .. tab-item:: Sync
        :sync: sync

        .. literalinclude:: /examples/testing/test_set_session_data.py
            :caption: Setting session data
            :language: python


        .. literalinclude:: /examples/testing/test_get_session_data.py
            :caption: Getting session data
            :language: python

    .. tab-item:: Async
        :sync: async

        .. literalinclude:: /examples/testing/test_set_session_data_async.py
            :caption: Setting session data
            :language: python


        .. literalinclude:: /examples/testing/test_get_session_data_async.py
            :caption: Getting session data
            :language: python


Using a blocking portal
+++++++++++++++++++++++

The :class:`TestClient <.testing.TestClient>` uses a feature of `anyio <https://anyio.readthedocs.io/en/stable/>`_ called
a **Blocking Portal**.

The :class:`anyio.abc.BlockingPortal` allows :class:`TestClient <.testing.TestClient>`
to execute asynchronous functions using a synchronous call. ``TestClient`` creates a blocking portal to manage
``Litestar``'s async logic, and it allows ``TestClient``'s API to remain fully synchronous.

Any tests that are using an instance of ``TestClient`` can also make use of the blocking portal to execute asynchronous functions
without the test itself being asynchronous.

.. literalinclude:: /examples/testing/test_with_portal.py
   :caption: Using a blocking portal
   :language: python


Creating a test app
-------------------

Litestar also offers a helper function called :func:`create_test_client <litestar.testing.create_test_client>` which first creates
an instance of Litestar and then a test client using it. There are multiple use cases for this helper - when you need to check
generic logic that is decoupled from a specific Litestar app, or when you want to test endpoints in isolation.

You can pass to this helper all the kwargs accepted by
the litestar constructor, with the ``route_handlers`` kwarg being **required**. Yet unlike the Litestar app, which
expects ``route_handlers`` to be a list, here you can also pass individual values.

For example, you can do this:

.. literalinclude:: /examples/testing/test_app_1.py
   :caption: my_app/tests/test_health_check.py
   :language: python


But also this:

.. literalinclude:: /examples/testing/test_app_2.py
   :caption: my_app/tests/test_health_check.py
   :language: python


RequestFactory
--------------

Another helper is the :class:`RequestFactory <litestar.testing.RequestFactory>` class, which creates instances of
:class:`litestar.connection.request.Request <litestar.connection.request.Request>`. The use case for this helper is when
you need to test logic that expects to receive a request object.

For example, lets say we wanted to unit test a *guard* function in isolation, to which end we'll reuse the examples
from the :doc:`route guards </usage/security/guards>` documentation:


.. literalinclude:: /examples/testing/test_request_factory_1.py
   :caption: my_app/guards.py
   :language: python


We already have our route handler in place:

.. literalinclude:: /examples/testing/test_request_factory_2.py
   :caption: my_app/secret.py
   :language: python


We could thus test the guard function like so:

.. literalinclude:: /examples/testing/test_request_factory_3.py
   :caption: tests/guards/test_secret_token_guard.py
   :language: python


Using polyfactory
------------------------

`Polyfactory <https://github.com/litestar-org/polyfactory>`__ offers an easy
and powerful way to generate mock data from pydantic models and dataclasses.

Let's say we have an API that talks to an external service and retrieves some data:

.. literalinclude:: /examples/testing/test_polyfactory_1.py
   :caption: main.py
   :language: python


We could test the ``/item`` route like so:

.. literalinclude:: /examples/testing/test_polyfactory_2.py
   :caption: tests/conftest.py
   :language: python


While we can define the test data manually, as is done in the above, this can be quite cumbersome. That's
where `polyfactory <https://github.com/litestar-org/polyfactory>`_ library comes in. It generates mock data for
pydantic models and dataclasses based on type annotations. With it, we could rewrite the above example like so:

.. literalinclude:: /examples/testing/test_polyfactory_3.py
   :caption: main.py
   :language: python
