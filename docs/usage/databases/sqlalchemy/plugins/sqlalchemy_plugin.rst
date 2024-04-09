SQLAlchemy Plugin
-----------------

The :class:`SQLAlchemyPlugin <advanced_alchemy.extensions.litestar.plugins.SQLAlchemyPlugin>` provides complete support for
working with `SQLAlchemy <https://www.sqlalchemy.org/>`_ in Litestar applications.

.. note::

    This plugin is only compatible with SQLAlchemy 2.0+.

The :class:`SQLAlchemyPlugin <advanced_alchemy.extensions.litestar.plugins.SQLAlchemyPlugin>` combines the functionality of
:class:`SQLAlchemyInitPlugin <advanced_alchemy.extensions.litestar.plugins.SQLAlchemyInitPlugin>` and
:class:`SQLAlchemySerializationPlugin <advanced_alchemy.extensions.litestar.plugins.SQLAlchemySerializationPlugin>`, each of
which are examined in detail in the following sections. As such, this section describes a complete example of using the
:class:`SQLAlchemyPlugin <advanced_alchemy.extensions.litestar.plugins.SQLAlchemyPlugin>` with a Litestar application and a
SQLite database.

Or, skip ahead to :doc:`/usage/databases/sqlalchemy/plugins/sqlalchemy_init_plugin` or
:doc:`/usage/databases/sqlalchemy/plugins/sqlalchemy_serialization_plugin` to learn more about the individual plugins.

.. tip::

    You can install SQLAlchemy alongside Litestar by running ``pip install litestar[sqlalchemy]``.

Example
=======

.. tab-set::

   .. tab-item:: Async

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_async_plugin_example.py
            :caption: SQLAlchemy Async Plugin Example
            :language: python
            :linenos:

   .. tab-item:: Sync

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_sync_plugin_example.py
            :caption: SQLAlchemy Sync Plugin Example
            :language: python
            :linenos:

Defining the Database Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We start by defining our base model class, and a ``TodoItem`` class which extends the base model. The ``TodoItem`` class
represents a todo item in our SQLite database.

.. tab-set::

   .. tab-item:: Async

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_async_plugin_example.py
            :caption: SQLAlchemy Async Plugin Example
            :language: python
            :lines: 6,15-24

   .. tab-item:: Sync

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_sync_plugin_example.py
            :caption: SQLAlchemy Sync Plugin Example
            :language: python
            :lines: 6,15-24

Setting Up an API Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, we set up an API endpoint at the root  (``"/"``)  that allows adding a ``TodoItem`` to the SQLite database.

.. tab-set::

   .. tab-item:: Async

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_async_plugin_example.py
            :caption: SQLAlchemy Async Plugin Example
            :language: python
            :lines: 3-5,8,10-14,25-31

   .. tab-item:: Sync

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_sync_plugin_example.py
            :caption: SQLAlchemy Sync Plugin Example
            :language: python
            :lines: 3-5,8,10-14,25-31

Initializing the Database
~~~~~~~~~~~~~~~~~~~~~~~~~

We create a function ``init_db`` that we'll use to initialize the database when the app starts up.

.. important::

    In this example we drop the database before creating it. This is done for the sake of repeatability, and should not
    be done in production.

.. tab-set::

   .. tab-item:: Async

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_async_plugin_example.py
            :caption: SQLAlchemy Async Plugin Example
            :language: python
            :lines: 8,32-37

   .. tab-item:: Sync

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_sync_plugin_example.py
            :caption: SQLAlchemy Sync Plugin Example
            :language: python
            :lines: 8,32-36

Setting Up the Plugin and the App
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, we set up the SQLAlchemy Plugin and the Litestar app.

.. tab-set::

   .. tab-item:: Async

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_async_plugin_example.py
            :caption: SQLAlchemy Async Plugin Example
            :language: python
            :lines: 8-9,38-41

   .. tab-item:: Sync

        .. literalinclude:: /examples/contrib/sqlalchemy/plugins/sqlalchemy_sync_plugin_example.py
            :caption: SQLAlchemy Sync Plugin Example
            :language: python
            :lines: 8-9,37-40

This configures the app with the plugin, sets up a route handler for adding items, and specifies that the ``init_db``
function should be run when the app starts up.

Running the App
~~~~~~~~~~~~~~~

Run the app with the following command:

.. code-block:: bash

    $ litestar run

You can now add a todo item by sending a POST request to ``http://localhost:8000`` with a JSON body containing the
``"title"`` of the todo item.

.. code-block:: bash

    $ curl -X POST -H "Content-Type: application/json" -d '{"title": "Your Todo Title", "done": false}' http://localhost:8000/
