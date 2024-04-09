Providing the session with DI
-----------------------------


In our original script, we had to repeat the logic to construct a session instance for every request type. This is not
very `DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_.

In this section, we'll use dependency injection to centralize the session creation logic and make it available to all
handlers.

.. literalinclude:: /examples/contrib/sqlalchemy/plugins/tutorial/full_app_with_session_di.py
    :language: python
    :linenos:
    :emphasize-lines: 47-57,82-83,87-89,94-95,103

In the previous example, the database session is created within each HTTP route handler function. In this script we use
dependency injection to decouple creation of the session from the route handlers.

This script introduces a new async generator function called ``provide_transaction()`` that creates a new SQLAlchemy
session, begins a transaction, and handles any integrity errors that might raise from within the transaction.

.. literalinclude:: /examples/contrib/sqlalchemy/plugins/tutorial/full_app_with_session_di.py
    :language: python
    :linenos:
    :lines: 48-57

That function is declared as a dependency to the Litestar application, using the name ``transaction``.

.. literalinclude:: /examples/contrib/sqlalchemy/plugins/tutorial/full_app_with_session_di.py
    :language: python
    :linenos:
    :lines: 101-105
    :emphasize-lines: 3

In the route handlers, the database session is injected by declaring the ``transaction`` name as a function argument.
This is automatically provided by Litestar's dependency injection system at runtime.


.. literalinclude:: /examples/contrib/sqlalchemy/plugins/tutorial/full_app_with_session_di.py
    :language: python
    :linenos:
    :lines: 81-84
    :emphasize-lines: 2

One final improvement in this script is exception handling. In the previous version, a
:class:`litestar.exceptions.ClientException` is raised inside the ``add_item()`` handler if there's an integrity error
raised during the insertion of the new TODO item. In our latest revision, we've been able to centralize this handling
to occur inside the ``provide_transaction()`` function.

.. literalinclude:: /examples/contrib/sqlalchemy/plugins/tutorial/full_app_with_session_di.py
    :language: python
    :linenos:
    :lines: 47-57
    :emphasize-lines: 3,6-10

This change broadens the scope of exception handling to any operation that uses the database session, not just the
insertion of new items.

Compare handlers before and after DI
====================================

Just for fun, lets compare the sets of application handlers before and after we introduced dependency injection for our
session object:

.. tab-set::

   .. tab-item:: After

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/tutorial/full_app_with_session_di.py
            :language: python
            :linenos:
            :lines: 81-105

   .. tab-item:: Before

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/tutorial/full_app_no_plugins.py
            :language: python
            :linenos:
            :lines: 69-100

Much better!

Next steps
==========

One of the niceties that we've lost is the ability to receive and return data to/from our handlers as instances of our
data model. In the original TODO application, we modelled with Python dataclasses which are natively supported for
(de)serialization by Litestar. In the next section, we will look at how we can get this functionality back!
