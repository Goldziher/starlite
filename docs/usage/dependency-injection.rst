Dependency Injection
====================

Litestar has a simple but powerful dependency injection system that allows for declaring dependencies on all layers of
the application:

.. literalinclude:: /examples/dependency_injection/dependency_base.py
    :caption: Dependency base example
    :language: python


The above example illustrates how dependencies are declared on the different layers of the application.

Dependencies can be either callables - sync or async functions, methods, or class instances that implement the
:meth:`object.__call__` method, or classes. These are in turn wrapped inside an instance of the
:class:`Provide <.di.Provide>` class.


.. include:: /admonitions/sync-to-thread-info.rst


Pre-requisites and scope
------------------------

The pre-requisites for dependency injection are these:


#. dependencies must be callables.
#. dependencies can receive kwargs and a ``self`` arg but not positional args.
#. the kwarg name and the dependency key must be identical.
#. the dependency must be declared using the ``Provide`` class.
#. the dependency must be in the *scope* of the handler function.

What is *scope* in this context? Dependencies are **isolated** to the context in which they are declared. Thus, in the
above example, the ``local_dependency`` can only be accessed within the specific route handler on which it was declared;
The ``controller_dependency`` is available only for route handlers on that specific controller; And the ``router
dependency`` is available only to the route handlers registered on that particular router. Only the ``app_dependency``
is available to all route handlers.

.. _yield_dependencies:

Dependencies with yield (cleanup step)
--------------------------------------

In addition to simple callables, dependencies can also be (async) generator functions, which allows
to execute an additional cleanup step, such as closing a connection, after the handler function
has returned.

.. admonition:: Technical details
    :class: info

    The cleanup stage is executed **after** the handler function returns, but **before** the
    response is sent (in case of HTTP requests)


A basic example
~~~~~~~~~~~~~~~

.. literalinclude:: /examples/dependency_injection/dependency_yield_simple.py
    :caption: Dependency yield simple
    :language: python


If you run the code you'll see that ``CONNECTION`` has been reset after the handler function
returned:

.. literalinclude:: /examples/dependency_injection/dependency_connection.py
    :caption: Dependency connection
    :language: python


Handling exceptions
~~~~~~~~~~~~~~~~~~~

If an exception occurs within the handler function, it will be raised **within** the
generator, at the point where it first ``yield`` ed. This makes it possible to adapt behaviour
of the dependency based on exceptions, for example rolling back a database session on error
and committing otherwise.

.. literalinclude:: /examples/dependency_injection/dependency_yield_exceptions.py
    :caption: Dependency yield exceptions
    :language: python


.. literalinclude:: /examples/dependency_injection/dependency_yield_exceptions_state.py
    :caption: Dependency yield exceptions states
    :language: python


.. admonition:: Best Practice
    :class: tip

    You should always wrap `yield` in a `try`/`finally` block, regardless of whether you
    want to handle exceptions, to ensure that the cleanup code is run even when exceptions
    occurred:

    .. literalinclude:: /examples/dependency_injection/dependency_yield_exceptions_trap.py
        :caption: Dependency with try/finally
        :language: python


.. attention::

   Do not re-raise exceptions within the dependency. Exceptions caught within these
   dependencies will still be handled by the regular mechanisms without an explicit
   re-raise


Dependency keyword arguments
----------------------------

As stated above dependencies can receive kwargs but no args. The reason for this is that dependencies are parsed using
the same mechanism that parses route handler functions, and they too - like route handler functions, can have data
injected into them.

In fact, you can inject the same data that you
can :ref:`inject into route handlers <usage/routing/handlers:"reserved" keyword arguments>`.

.. literalinclude:: /examples/dependency_injection/dependency_keyword_arguments.py
    :caption: Dependency keyword arguments
    :language: python


In the above example we have a ``User`` model that we are persisting into a db. The model is fetched using the helper
method ``retrieve_db_user`` which receives a ``user_id`` kwarg and retrieves the corresponding ``User`` instance.
The ``UserController`` class maps the ``retrieve_db_user`` provider to the key ``user`` in its ``dependencies`` dictionary. This
in turn makes it available as a kwarg in the ``get_user`` method.




Dependency overrides
--------------------

Because dependencies are declared at each level of the app using a string keyed dictionary, overriding dependencies is
very simple:

.. literalinclude:: /examples/dependency_injection/dependency_overrides.py
    :caption: Dependency overrides
    :language: python


The lower scoped route handler function declares a dependency with the same key as the one declared on the higher scoped
controller. The lower scoped dependency therefore overrides the higher scoped one.


The ``Provide`` class
----------------------

The :class:`Provide <.di.Provide>` class is a wrapper used for dependency injection. To inject a callable you must wrap
it in ``Provide``:

.. literalinclude:: /examples/dependency_injection/dependency_provide.py
    :caption: Dependency with Provide
    :language: python


.. attention::

    If :class:`Provide.use_cache <.di.Provide>` is ``True``, the return value of the function will be memoized the first
    time it is called and then will be used. There is no sophisticated comparison of kwargs, LRU implementation, etc., so
    you should be careful when you choose to use this option. Note that dependencies will only be called once per
    request, even with ``Provide.use_cache`` set to ``False``.



Dependencies within dependencies
--------------------------------

You can inject dependencies into other dependencies - exactly like you would into regular functions.

.. literalinclude:: /examples/dependency_injection/dependency_within_dependency.py
    :caption: Dependencies within dependencies
    :language: python


.. note::

   The rules for `dependency overrides`_ apply here as well.


The ``Dependency`` function
----------------------------

Dependency validation
~~~~~~~~~~~~~~~~~~~~~

By default, injected dependency values are validated by Litestar, for example, this application will raise an
internal server error:

.. literalinclude:: /examples/dependency_injection/dependency_validation_error.py
    :caption: Dependency validation error
    :language: python


Dependency validation can be toggled using the :class:`Dependency <litestar.params.Dependency>` function.

.. literalinclude:: /examples/dependency_injection/dependency_skip_validation.py
    :caption: Dependency validation error
    :language: python


This may be useful for reasons of efficiency, or if pydantic cannot validate a certain type, but use with caution!

Dependency function as a marker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`Dependency <litestar.params.Dependency>` function can also be used as a marker that gives us a bit more detail
about your application.

Exclude dependencies with default values from OpenAPI docs
***********************************************************

Depending on your application design, it is possible to have a dependency declared in a handler or
:class:`Provide <.di.Provide>` function that has a default value. If the dependency isn't provided for the route, the
default should be used by the function.

.. literalinclude:: /examples/dependency_injection/dependency_with_default.py
    :caption: Dependency with default value
    :language: python


This doesn't fail, but due to the way the application determines parameter types, it is inferred to be a query
parameter.


By declaring the parameter to be a dependency, Litestar knows to exclude it from the docs:

.. literalinclude:: /examples/dependency_injection/dependency_with_dependency_fn_and_default.py
    :caption: Dependency with default value
    :language: python


Early detection if a dependency isn't provided
***********************************************

The other side of the same coin is when a dependency isn't provided, and no default is specified. Without the dependency
marker, the parameter is assumed to be a query parameter and the route will most likely fail when accessed.

If the parameter is marked as a dependency, this allows us to fail early instead:

.. literalinclude:: /examples/dependency_injection/dependency_non_optional_not_provided.py
   :caption: Dependency not provided error
   :language: python
